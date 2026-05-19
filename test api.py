import requests

# ===== 配置区域 =====
API_KEY = ""
BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL = "Qwen/Qwen2.5-7B-Instruct"


# ===================

def test_call():
    """最简 API 调用测试"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "请把这句话用温和、不制造焦虑的语气重写一遍：CPU温度78°C，GPU占用率99%。只输出重写后的一句话。"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }

    try:
        print("正在调用 API，请稍候...")
        response = requests.post(BASE_URL, headers=headers, json=data, timeout=15)
        response.raise_for_status()  # 如果状态码不是 200，抛出异常

        result = response.json()
        reply = result["choices"][0]["message"]["content"].strip()

        print("\n✅ 调用成功！")
        print(f"AI 回复：{reply}")
        return reply

    except requests.exceptions.ConnectionError:
        print("❌ 网络连接失败，请检查网络或代理设置")
    except requests.exceptions.Timeout:
        print("❌ 请求超时，请稍后重试")
    except Exception as e:
        print(f"❌ 调用失败：{e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"服务器返回：{e.response.text}")

    return None


if __name__ == "__main__":
    test_call()