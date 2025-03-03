from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

from clean import clean_html
from convert import convert_html
from fastapi import HTTPException
import requests
from fastapi.responses import StreamingResponse

app = FastAPI()

# 读入env文件
load_dotenv(find_dotenv())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Item(BaseModel):
    """
    Args:
        html (str): 输入的HTML文本
        stream (bool): 是否使用流式响应
        require (str): 输入的问题
    """

    html: str | None = None
    stream: bool = True
    require_agent: str | None = None
    require_workflow: str | None = None


@app.post("/v1/navi")
async def process_item(item: Item):
    if item.require_agent is not None:
        # 此处调用智能客服
        agent_url = os.getenv("AGENT_URL", "")
        key = "Bearer " + os.getenv("DIFY_KEY_AGENT_ZARO", "key-simple")
        headers = {"Authorization": key, "Content-Type": "application/json"}
        user = os.getenv("DIFY_USER", "default")

        data = {
            "inputs": {},
            "query": item.require_agent,
            "response_mode": "streaming",
            "conversation_id": "",
            "user": user + "agent",
        }

        try:
            print("正在运行agent", agent_url)
            response = requests.post(agent_url, headers=headers, json=data, stream=True)
            # 检查Dify平台的响应状态
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, detail="Dify API request failed"
                )

            # 定义生成器函数，用于逐步转发Dify的流式响应
            def generate():
                for chunk in response.iter_content(chunk_size=None):
                    if chunk:
                        yield chunk

            # 使用StreamingResponse实现流式转发
            return StreamingResponse(
                generate(),
                media_type=response.headers.get("Content-Type", "text/event-stream"),
            )
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return HTTPException(status_code=500, detail=str(e))
    elif (item.html is not None) or (item.require_workflow is not None):
        workflow_url = os.getenv("WORKFLOW_URL", "http://localhost:18111")
        key = os.getenv("DIFY_KEY_WORKFLOW_ZERO", "")
        key = "Bearer " + key
        headers = {"Authorization": key, "Content-Type": "application/json"}
        user = os.getenv("DIFY_USER", "default")

        data = {
            "inputs": {"text_input": None, "web_page": None},
            "response_mode": "streaming" if item.stream else "blocking",
            "user": user + "workflow",
        }

        if item.require_workflow is not None:
            data["inputs"]["text_input"] = item.require_workflow
        else:
            html_cleaned = await clean_html(item.html)
            html_md = convert_html(html_cleaned)
            data["inputs"]["text_input"] = "none"
            data["inputs"]["web_page"] = html_md
        if item.stream:
            try:
                print("运行工作流streaming...", workflow_url)
                print("data", data)
                response = requests.post(
                    workflow_url, headers=headers, json=data, stream=True
                )

                # 检查Dify平台的响应状态
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Dify API request failed",
                    )

                # 定义生成器函数，用于逐步转发Dify的流式响应
                def generate():
                    for chunk in response.iter_content(chunk_size=None):
                        if chunk:
                            yield chunk

                # 使用StreamingResponse实现流式转发
                return StreamingResponse(
                    generate(),
                    media_type=response.headers.get(
                        "Content-Type", "text/event-stream"
                    ),
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        else:
            try:
                print("运行工作流blocking...")
                response = requests.post(workflow_url, headers=headers, json=data)
                if response.status_code == 200:
                    print("工作流执行成功")
                    return response.json()
                else:
                    print(f"工作流执行失败，状态码: {response.status_code}")
                    return {
                        "status": "error",
                        "message": f"Failed to execute workflow, status code: {response.status_code}",
                    }
            except Exception as e:
                print(f"发生错误: {str(e)}")
                return HTTPException(status_code=500, detail=str(e))


# 启动服务
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 18111))
    uvicorn.run(app, host="0.0.0.0", port=port)
