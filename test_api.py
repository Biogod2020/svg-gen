import requests
import json

def test_svg_api(prompt: str):
    url = "http://localhost:8000/generate"
    payload = {
        "prompt": prompt,
        "style_hints": "Use a professional, clean corporate color palette (blues and grays)."
    }
    
    print(f"🚀 发送请求到 API: {prompt}")
    try:
        response = requests.post(url, json=payload, timeout=300) # 考虑到审计循环，超时设长一点
        if response.status_code == 200:
            result = response.json()
            print("✅ 生成成功!")
            print(f"Job ID: {result['job_id']}")
            print(f"VQA 状态: {result['vqa_status']}")
            print(f"生成的图注: {result['caption']}")
            
            # 验证 history 字段
            if "history" in result:
                history = result["history"]
                print(f"📈 迭代历史长度: {len(history)}")
                for i, entry in enumerate(history):
                    print(f"  Iteration {i}:")
                    print(f"    - SVG 长度: {len(entry.get('svg_code', ''))}")
                    print(f"    - VQA 状态: {entry.get('vqa_results', {}).get('status')}")
                    print(f"    - PNG (b64) 长度: {len(entry.get('png_b64', ''))}")
            else:
                print("❌ 响应中缺少 'history' 字段!")
            
            # 保存结果到本地查看
            with open("test_output.svg", "w", encoding="utf-8") as f:
                f.write(result['svg'])
            print("💾 SVG 已保存 to test_output.svg")
        else:
            print(f"❌ 请求失败 ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ 发生异常: {e}")

if __name__ == "__main__":
    test_svg_api("A modern, minimalist network architecture diagram showing 3 layers: Core, Aggregation, and Access.")
