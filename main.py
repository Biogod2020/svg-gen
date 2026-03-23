import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.agents.svg_generation.agent import SVGAgent
from src.core.types import AgentState
from src.core.gemini_client import GeminiClient

app = FastAPI(title="SVG Optimization Lab API")

# 初始化核心组件
client = GeminiClient()
agent = SVGAgent(client=client)

class SvgRequest(BaseModel):
    prompt: str
    style_hints: Optional[str] = ""

@app.post("/generate")
async def generate_svg(request: SvgRequest):
    """
    一键生成经过 VLM 审计和修复的高质量 SVG。
    """
    # 1. 为本次请求创建唯一的任务 ID 和临时工作空间
    job_id = f"api_{uuid.uuid4().hex[:8]}"
    workspace_path = Path("workspace") / job_id
    workspace_path.mkdir(parents=True, exist_ok=True)

    # 2. 初始化 Agent 状态
    state = AgentState(
        job_id=job_id,
        workspace_path=str(workspace_path)
    )

    try:
        print(f"[API] 接收到生成请求: {request.prompt[:50]}...")
        
        # 3. 执行 SVGAgent 的闭环优化逻辑
        success, asset, html = await agent.run_optimization_loop(
            asset_id=f"svg_{job_id}",
            description=request.prompt,
            state=state,
            style_hints=request.style_hints
        )

        if not success or not asset:
            raise HTTPException(status_code=500, detail="SVG Generation or Optimization failed.")

        # 4. 从资产库中读取最终生成的 SVG 代码
        svg_path = workspace_path / asset.local_path
        if not svg_path.exists():
             raise HTTPException(status_code=500, detail="Generated SVG file not found on disk.")
             
        svg_code = svg_path.read_text(encoding="utf-8")
        
        return {
            "job_id": job_id,
            "svg": svg_code,
            "vqa_status": asset.vqa_status,
            "caption": asset.caption,
            "history": agent.history
        }

    except Exception as e:
        print(f"[API] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 默认启动在 8000 端口
    uvicorn.run(app, host="0.0.0.0", port=8000)
