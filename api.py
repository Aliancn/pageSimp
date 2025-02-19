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
    html: str
    stream: bool = False


@app.post("/pagenavi/")
async def process_item(item: Item):
    html_cleaned = await clean_html(item.html)
    html_md = convert_html(html_cleaned)

    workflow_url = os.getenv("WORKFLOW_URL")
    key = os.getenv("DIFY_KEY")
    key = "Bearer " + key
    headers = {
        "Authorization": key,
        "Content-Type": "application/json"
    }
    user = os.getenv("DIFY_USER")

    data = {
        "inputs": {
            "text_input": "ali",
            "web_page": html_md
        },
        "response_mode": "streaming" if item.stream else "blocking",
        "user": user
    }

    if item.stream:
        try:
            print("运行工作流streaming...")
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
    else:
        try:
            print("运行工作流blocking...")
            response = requests.post(workflow_url, headers=headers, json=data)
            if response.status_code == 200:
                print("工作流执行成功")
                return response.json()
            else:
                print(f"工作流执行失败，状态码: {response.status_code}")
                return {"status": "error", "message": f"Failed to execute workflow, status code: {response.status_code}"}
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return HTTPException(status_code=500, detail=str(e))


# 启动服务
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 18001))
    uvicorn.run(app, host="0.0.0.0", port=port)
