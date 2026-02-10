
import requests
import json
from modules.radiofrance_api import RadioFranceClient, API_BASE_URL, HEADERS

def debug_mozart():
    query = "Les Odyssées symphoniques"
    print(f"Searching for: {query}")
    
    # 1. Search to get ID
    results = RadioFranceClient.search_shows(query)
    target_show = None
    for res in results:
        print(f"Found: {res['title']} (ID: {res['id']})")
        if "Mozart" in res['title'] or "symphoniques" in res['title']:
            target_show = res
            break
            
    if not target_show:
        print("Could not find target show in search results.")
        return

    show_id = target_show['id']
    print(f"\nTarget Show ID: {show_id}")
    print(f"Target Title: {target_show['title']}")
    print(f"Target Visuals: {list(target_show.get('visuals', {}).keys())}")
    print(f"Target MainImage: {target_show.get('mainImage')}")

    # 2. Fetch Feed (Diffusions) and Fallback
    print(f"\nFetching Feed for {show_id}...")
    
    # Mimic get_feed logic but print debug info
    url = f"{API_BASE_URL}/shows/{show_id}/diffusions"
    params = {
        "filter[manifestations][exists]": "true",
        "include": ["show", "manifestations"],
        "page[offset]": 0
    }
    
    try:
        resp = requests.get(url, headers=HEADERS, params=params)
        print(f"Diffusions Status: {resp.status_code}")
        data = resp.json()
        
        print("\n--- Diffusions Response 'included' ---")
        if 'included' in data and 'shows' in data['included']:
             shows_inc = data['included']['shows']
             if show_id in shows_inc:
                 s = shows_inc[show_id]
                 print(f"Show found in included: {s.get('title')}")
                 print(f"Visuals: {list(s.get('visuals', {}).keys())}")
             else:
                 print(f"Show ID {show_id} NOT found in included/shows")
                 print(f"IDs present: {list(shows_inc.keys())}")
        else:
             print("'included/shows' missing or empty")

        # Fallback check
        print("\n--- Checking Fallback /shows/{id} ---")
        fb_url = f"{API_BASE_URL}/shows/{show_id}"
        resp_fb = requests.get(fb_url, headers=HEADERS)
        if resp_fb.ok:
            fb_data = resp_fb.json().get('data', {})
            print(f"Fallback Keys: {list(fb_data.keys())}")
            
            if 'shows' in fb_data:
                print(f"Fallback 'shows' keys: {list(fb_data['shows'].keys())}")
                if show_id in fb_data['shows']:
                    s = fb_data['shows'][show_id]
                    print(f"Show matched by ID. Visuals: {list(s.get('visuals', {}).keys())}")
                else:
                    print(f"Show ID {show_id} NOT in 'shows' keys!")
            
            # Recursive search for title string
            def find_val(data, target):
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, str) and target in v:
                            print(f"Found '{target}' in key: {k}, value: {v}")
                        find_val(v, target)
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        find_val(item, target)
            
            print("\nSearching for 'Mozart' in fallback data:")
            find_val(fb_data, "Mozart")
            
            print("\nSearching for 'symphoniques' in fallback data:")
            find_val(fb_data, "symphoniques")

        else:
            print(f"Fallback Status: {resp_fb.status_code}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    with open("debug_output_utf8.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        debug_mozart()
