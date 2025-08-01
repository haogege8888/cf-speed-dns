import requests
import traceback
import time
import os
import json
import subprocess

# API 密钥
CF_API_TOKEN    = os.environ["CF_API_TOKEN"]
CF_ZONE_ID      = os.environ["CF_ZONE_ID"]
CF_DNS_NAME     = os.environ["CF_DNS_NAME"]
PUSHPLUS_TOKEN  = os.environ["PUSHPLUS_TOKEN"]

headers = {
    'Authorization': f'Bearer {CF_API_TOKEN}',
    'Content-Type': 'application/json'
}

def get_cf_speed_test_ip(timeout=10, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = requests.get('https://ip.164746.xyz/ipTop.html', timeout=timeout)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            traceback.print_exc()
            print(f"get_cf_speed_test_ip Request failed (attempt {attempt + 1}/{max_retries}): {e}")
    return None

def get_dns_records(name):
    def_info = []
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json()['result']
        for record in records:
            if record['name'] == name:
                def_info.append(record['id'])
        return def_info
    else:
        print('Error fetching DNS records:', response.text)

def update_dns_record(record_id, name, cf_ip):
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{record_id}'
    data = {
        'type': 'A',
        'name': name,
        'content': cf_ip
    }
    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"cf_dns_change success: ---- Time: {time.strftime('%Y-%m-%d %H:%M:%S')} ---- ip：{cf_ip}")
        return f"ip:{cf_ip} 解析 {name} 成功"
    else:
        print(f"cf_dns_change ERROR: ---- Time: {time.strftime('%Y-%m-%d %H:%M:%S')} ---- MESSAGE: {response.text}")
        return f"ip:{cf_ip} 解析 {name} 失败"

def push_plus(content):
    url = 'http://www.pushplus.plus/send'
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": "IP优选DNSCF推送",
        "content": content,
        "template": "markdown",
        "channel": "wechat"
    }
    try:
        body = json.dumps(data).encode(encoding='utf-8')
        headers = {'Content-Type': 'application/json'}
        requests.post(url, data=body, headers=headers)
    except Exception as e:
        print("PushPlus 推送失败：", e)

def git_commit_push():
    try:
        subprocess.run(["git", "config", "--global", "user.name", "Auto Bot"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "bot@example.com"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"自动化提交: {time.strftime('%Y-%m-%d %H:%M:%S')}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Git 提交成功")
    except subprocess.CalledProcessError:
        print("Git：无变更或提交失败（可能无差异或权限不足）")

def main():
    ip_addresses_str = get_cf_speed_test_ip()
    if not ip_addresses_str:
        print("未获取到优选 IP，终止流程")
        return

    ip_addresses = ip_addresses_str.split(',')
    dns_records = get_dns_records(CF_DNS_NAME)
    push_plus_content = []

    for index, ip_address in enumerate(ip_addresses):
        dns = update_dns_record(dns_records[index], CF_DNS_NAME, ip_address)
        push_plus_content.append(dns)

    push_plus('\n'.join(push_plus_content))

    # 新增 Git 提交推送
    git_commit_push()

if __name__ == '__main__':
    main()
