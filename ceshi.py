import requests

def get_cpu_temperature():
    try:
        response = requests.get('http://localhost:8085/data.json', timeout=3)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[CPU温度] 请求失败: {e}")
        return None

    # 根据你打印的结构，定向查找 CPU
    children = data.get('Children', [])
    if not children:
        print("[CPU温度] 没有 Children")
        return None

    hw_list = children[0].get('Children', [])
    cpu_node = None
    for hw in hw_list:
        if '5600X' in hw.get('Text', '') or 'CPU' in hw.get('Text', ''):
            cpu_node = hw
            break

    if not cpu_node:
        print("[CPU温度] 未找到 CPU 节点")
        return None

    # 遍历 CPU 的所有子孙传感器，找温度
    def find_temps(node):
        if isinstance(node, dict):
            if node.get('SensorType') == 'Temperature':
                val = node.get('Value')
                if isinstance(val, (int, float)):
                    return [(node.get('Text', '?'), val)]
            for child in node.get('Children', []):
                yield from find_temps(child)

    temps = []
    for child in cpu_node.get('Children', []):
        temps.extend(find_temps(child))

    print(f"CPU 温度传感器: {temps}")

    # 优先选值 > 0 的
    for name, val in temps:
        if val > 0:
            return round(val, 1)

    # 如果全是 0，就先返回 0（总比 None 强）
    if temps:
        print("[CPU温度] 所有传感器都是 0.0，返回 0")
        return 0.0

    print("[CPU温度] 未找到任何温度传感器")
    return None