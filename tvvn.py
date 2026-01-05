# -*- coding: UTF-8 -*-
import os, re, sys, json, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, xbmc
import urllib.parse as urllib_parse
import urllib.request as urllib_request

addon = xbmcaddon.Addon('plugin.video.tvvn')
home = xbmcvfs.translatePath(addon.getAddonInfo('path'))
datafile = xbmcvfs.translatePath(os.path.join(home, 'data.json'))

with open(datafile, "r", encoding="utf8") as f:
    data = json.loads(f.read())

def get_params():
    param = {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        pairs = paramstring.replace('?', '').split('&')
        for p in pairs:
            split = p.split('=')
            if len(split) == 2: param[split[0]] = split[1]
    return param

def construct_menu(namex):
    menu_items = data['directories'][namex]['content']
    
    # Sắp xếp: All đầu, Oversea/International cuối
    all_items = [i for i in menu_items if "all" in str(i.get('id','')).lower()]
    inter_items = [i for i in menu_items if any(x in str(i.get('id','')).lower() for x in ["oversea", "international"])]
    others = [i for i in menu_items if i not in all_items and i not in inter_items]
    
    sorted_list = all_items + others + inter_items

    for item in sorted_list:
        iid = item['id']
        if item['type'] in ["chn", "chn_"]:
            info = data['channels'][iid]
            url = f"{sys.argv[0]}?mode=1&chn={iid}"
            liz = xbmcgui.ListItem(info['title'])
            liz.setInfo(type="video", infoLabels={"title": info['title']})
            liz.setProperty('IsPlayable', 'true') # Cực kỳ quan trọng
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
        elif item['type'] in ["dir", "dir_"]:
            info = data['directories'][iid]
            url = f"{sys.argv[0]}?mode=2&chn={iid}"
            liz = xbmcgui.ListItem(f"[B]{info['title']}[/B]")
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=True)
            
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def play_link(chn_id):
    chn = data['channels'][chn_id]
    play_type = chn['src']['playpath']
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    full_url = ""

    try:
        if play_type == "m3u8_vtvgo":
            page_url = chn['src']['page_url']
            headers = {'User-Agent': ua, 'Referer': 'https://vtvgo.vn/'}
            req = urllib_request.Request(page_url, headers=headers)
            html = urllib_request.urlopen(req, timeout=7).read().decode('utf-8')
            
            # Cách lấy link mới: Tìm link m3u8 trực tiếp trong mã nguồn
            links = re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', html)
            if links:
                # Chọn link đầu tiên tìm thấy và thêm bảo mật
                full_url = f"{links[0]}|User-Agent={ua}&Referer=https://vtvgo.vn/&Origin=https://vtvgo.vn"
            else:
                # Tìm theo kiểu cũ nếu kiểu mới không có
                match = re.search(r"link\s*[:=]\s*['\"](.*?)['\"]", html)
                if match:
                    full_url = f"{match.group(1)}|User-Agent={ua}&Referer=https://vtvgo.vn/"

        elif play_type == "m3u8_tvnet":
            page_id = chn['src']['page_id']
            api_url = f"http://au.tvnet.gov.vn/kenh-truyen-hinh/{page_id}"
            req = urllib_request.Request(api_url, headers={'User-Agent': ua})
            html = urllib_request.urlopen(req, timeout=7).read().decode('utf-8')
            match = re.search(r'data-file="(.*?)"', html)
            if match:
                full_url = f"{match.group(1)}|User-Agent={ua}"

    except: pass

    if full_url:
        # Lệnh quan trọng để Kodi thoát trạng thái "Đang kết nối" và bắt đầu phát
        liz = xbmcgui.ListItem(path=full_url)
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)
    else:
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=False, listitem=xbmcgui.ListItem())
        xbmcgui.Dialog().notification("Lỗi", "Không tìm thấy nguồn phát", xbmcgui.NOTIFICATION_ERROR)

# --- Main ---
params = get_params()
mode = params.get('mode')
chn_id = params.get('chn')

if mode is None:
    construct_menu("root")
elif int(mode) == 1:
    play_link(chn_id)
elif int(mode) == 2:
    construct_menu(chn_id)

