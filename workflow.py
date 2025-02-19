import requests
from fastapi.responses import StreamingResponse
from fastapi import HTTPException


def run_workflow(web_page: str, user="aliancn", response_mode="blocking"):
    workflow_url = "http://127.0.0.1:8080/v1/workflows/run"
    headers = {
        "Authorization": "Bearer app-AUOTCiIjV9cZIclD0aUzMd9Z",
        "Content-Type": "application/json"
    }

    data = {
        "inputs": {
            "text_input": "ali",
            "web_page": web_page
        },
        "response_mode": response_mode,
        "user": user
    }

    try:
        print("运行工作流...")
        response = requests.post(workflow_url, headers=headers, json=data)
        if response.status_code == 200:
            print("工作流执行成功")
            return response.json()
        else:
            print(f"工作流执行失败，状态码: {response.status_code}")
            return {"status": "error", "message": f"Failed to execute workflow, status code: {response.status_code}"}
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return {"status": "error", "message": str(e)}


async def run_workflow_stream(web_page: str, user="aliancn", response_mode="streaming"):
    try:
        workflow_url = "http://127.0.0.1:8080/v1/workflows/run"
        headers = {
            "Authorization": "Bearer app-AUOTCiIjV9cZIclD0aUzMd9Z",
            "Content-Type": "application/json"
        }

        data = {
            "inputs": {
                "text_input": "ali",
                "web_page": web_page
            },
            "response_mode": response_mode,
            "user": user
        }

        response = requests.post(
            workflow_url, headers=headers, json=data, stream=True)

        # 检查Dify平台的响应状态
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail="Dify API request failed")

        # 定义生成器函数，用于逐步转发Dify的流式响应
        def generate():
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    yield chunk

        # 使用StreamingResponse实现流式转发
        return StreamingResponse(
            generate(),
            media_type=response.headers.get(
                "Content-Type", "application/json")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# test
md_test_text = """
需求大厅

服务大厅

需求类型

全部

物流仓储类

金融类

采购类

技术类

需求细分

全部

搜 索

发布需求

中欧回程，俄罗斯舒沙雷发往中国吴家山

中欧回程，俄罗斯舒沙雷发往中国吴家山"""
print(run_workflow_stream(md_test_text))
