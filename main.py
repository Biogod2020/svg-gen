import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Union, List, Dict, Any
import json

from src.agents.svg_generation.agent import SVGAgent
from src.core.types import AgentState, AssetVQAStatus
from src.core.gemini_client import GeminiClient

app = FastAPI(title="SVG Optimization Lab API")

# 初始化核心组件
client = GeminiClient()

class SvgRequest(BaseModel):
    prompt: str
    style_hints: Optional[Union[str, List[str]]] = ""

class SvgResponse(BaseModel):
    job_id: str
    svg: str
    vqa_status: AssetVQAStatus
    caption: str
    history: List[Dict[str, Any]]

@app.post("/generate", response_model=SvgResponse)
async def generate_svg(request: SvgRequest):
    """
    一键生成经过 VLM 审计和修复的高质量 SVG。
    """
    # 1. 为本次请求创建唯一的任务 ID 和临时工作空间
    job_id = f"api_{uuid.uuid4().hex[:8]}"
    workspace_path = Path("workspace") / job_id
    workspace_path.mkdir(parents=True, exist_ok=True)

    # 2. 初始化 Agent 状态和独立的 SVGAgent 实例
    state = AgentState(
        job_id=job_id,
        workspace_path=str(workspace_path)
    )
    # 每次请求实例化一个独立的 Agent，避免历史记录状态共享冲突
    agent = SVGAgent(client=client)

    # Convert style_hints to string if it's a list
    style_hints = request.style_hints
    if isinstance(style_hints, list):
        style_hints = ", ".join(style_hints)

    try:
        print(f"[API] 接收到生成请求: {request.prompt[:50]}...")
        
        # 3. 执行 SVGAgent 的闭环优化逻辑
        async for iteration in agent.run_optimization_loop(
            asset_id=f"svg_{job_id}",
            description=request.prompt,
            state=state,
            style_hints=style_hints
        ):
            pass

        uar = state.get_uar()
        asset = uar.assets.get(f"svg_{job_id}")

        if not asset:
            raise HTTPException(status_code=500, detail="SVG Generation or Optimization failed.")

        # 4. 从资产库中读取最终生成的 SVG 代码
        svg_path = Path(state.workspace_path) / asset.local_path
        if not svg_path.exists():
             raise HTTPException(status_code=500, detail="Generated SVG file not found on disk.")
             
        svg_code = svg_path.read_text(encoding="utf-8")
        
        return SvgResponse(
            job_id=job_id,
            svg=svg_code,
            vqa_status=asset.vqa_status,
            caption=asset.caption,
            history=agent.history
        )

    except Exception as e:
        print(f"[API] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-stream")
async def generate_svg_stream(request: SvgRequest):
    """
    流式生成 SVG。通过 SSE (Server-Sent Events) 返回每一轮迭代的结果。
    """
    job_id = f"api_{uuid.uuid4().hex[:8]}"
    workspace_path = Path("workspace") / job_id
    workspace_path.mkdir(parents=True, exist_ok=True)

    state = AgentState(
        job_id=job_id,
        workspace_path=str(workspace_path)
    )
    agent = SVGAgent(client=client)

    # Convert style_hints to string if it's a list
    style_hints = request.style_hints
    if isinstance(style_hints, list):
        style_hints = ", ".join(style_hints)

    async def event_generator():
        try:
            print(f"[API] 接收到流式生成请求: {request.prompt[:50]}...")
            async for iteration in agent.run_optimization_loop(
                asset_id=f"svg_{job_id}",
                description=request.prompt,
                state=state,
                style_hints=style_hints
            ):
                # Ensure iteration data is serializable
                # vqa_results is an AuditResult object, need to convert to dict
                if hasattr(iteration.get("vqa_results"), "model_dump"):
                    iteration["vqa_results"] = iteration["vqa_results"].model_dump()
                
                yield f"data: {json.dumps(iteration)}\n\n"
            
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"[API] Stream Error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    # 默认启动在 8000 端口
    uvicorn.run(app, host="0.0.0.0", port=8000)
