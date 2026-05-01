"""天气查询（Open-Meteo + Nominatim）"""
import re
import time
import requests
from modules.config import PROXY_URL, logger

WEATHER_PATTERN = re.compile(r'(.+?)(?:的|市|省|区)?天气', re.IGNORECASE)

WEATHER_MAP = {
    0: '晴朗', 1: '大致晴朗', 2: '局部多云', 3: '多云',
    45: '有雾', 48: '有雾',
    51: '细雨', 53: '细雨', 55: '细雨',
    61: '小雨', 63: '中雨', 65: '大雨',
    71: '小雪', 73: '中雪', 75: '大雪',
    80: '阵雨', 81: '阵雨', 82: '强阵雨',
    95: '雷雨', 96: '雷雨', 99: '强雷雨',
}


def get_coordinates(city_name: str) -> tuple[float | None, float | None]:
    """通过 Nominatim API 获取经纬度"""
    url = 'https://nominatim.openstreetmap.org/search'
    params = {'q': city_name, 'format': 'json', 'limit': 1, 'accept-language': 'zh'}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    proxies = {'http': PROXY_URL, 'https': PROXY_URL}
    try:
        time.sleep(1)
        resp = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
        logger.warning(f'地理编码失败，状态码: {resp.status_code}')
    except Exception as e:
        logger.error(f'地理编码异常: {e}')
    return None, None


def get_weather_by_city(city_name: str) -> str:
    """查询天气，返回流萤风格的天气描述"""
    start_time = time.time()
    logger.info(f'查询天气: {city_name}')
    lat, lon = get_coordinates(city_name)
    if lat is None:
        return f'嗯……我找不到 {city_name} 这个地方呢。要不说说你现在的城市？'

    url = 'https://api.open-meteo.com/v1/forecast'
    params = {
        'latitude': lat,
        'longitude': lon,
        'current': ['temperature_2m', 'weather_code', 'wind_speed_10m'],
        'timezone': 'auto',
    }
    proxies = {'http': PROXY_URL, 'https': PROXY_URL}
    try:
        resp = requests.get(url, params=params, proxies=proxies, timeout=10)
        if resp.status_code != 200:
            logger.error(f'天气API失败 ({resp.status_code})')
            return '天气数据获取失败了……是星核干扰吗？'
        data = resp.json()
        current = data.get('current', {})
        temp = current.get('temperature_2m')
        weather_code = current.get('weather_code')
        wind = current.get('wind_speed_10m')
        weather_desc = WEATHER_MAP.get(weather_code, '未知天气')

        note_map = {
            '雷雨': '…雷声好响。要一起躲雨吗？',
            '晴朗': '天气真好呢。要是能一起看星星就好了……虽然现在还是白天。',
            '多云': '云有点多……不过没关系，云后面还是会有星星的。',
        }
        note = note_map.get(weather_desc, '')
        if not note and '雨' in weather_desc:
            note = '下雨了……（轻声）银狼说雨天适合吃蛋糕。'
        if not note and weather_desc == '有雾':
            note = '起雾了。像梦一样……不过我还是更喜欢看星星。'

        reply = f'{city_name}现在{weather_desc}，气温{temp:.0f}度'
        if wind > 20:
            reply += '，风有点大呢'
        reply += '。' + note
        logger.info(f'天气查询完成，耗时 {time.time() - start_time:.2f} 秒')
        return reply
    except Exception as e:
        logger.error(f'天气API异常: {e}', exc_info=True)
        return '天气数据获取失败了……是星核干扰吗？'
