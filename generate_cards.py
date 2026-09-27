import os
import requests
import matplotlib.pyplot as plt
from collections import defaultdict

TOKEN = os.getenv("GH_TOKEN")
USERNAME = "sanmitramukherjee"

if not TOKEN:
    raise ValueError("GH_TOKEN secret is missing!")

query = """
query($login: String!, $endCursor: String) {
  user(login: $login) {
    repositories(first: 100, after: $endCursor, ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
        isFork
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
"""

def fetch_repositories():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    repos = []
    has_next_page = True
    end_cursor = None
    
    while has_next_page:
        variables = {"login": USERNAME, "endCursor": end_cursor}
        response = requests.post("https://github.com", json={"query": query, "variables": variables}, headers=headers)
        if response.status_code != 200:
            raise Exception(f"GraphQL Query failed: {response.text}")
        data = response.json()["data"]["user"]["repositories"]
        repos.extend(data["nodes"])
        has_next_page = data["pageInfo"]["hasNextPage"]
        end_cursor = data["pageInfo"]["endCursor"]
    return repos

def main():
    repos = fetch_repositories()
    lang_counts = defaultdict(int)
    lang_colors = {}
    
    EXCLUDED_REPOS = ["WeevilsPlanner", "WeevilsPlanner-lite"]
    
    for repo in repos:
        if repo["name"] in EXCLUDED_REPOS:
            continue
            
        for edge in repo["languages"]["edges"]:
            lang_name = edge["node"]["name"]
            lang_color = edge["node"]["color"]
            lang_counts[lang_name] += edge["size"]
            if lang_color:
                lang_colors[lang_name] = lang_color

    if not lang_counts:
        return

    # Extract top 5 languages
    sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    labels = [x[0] for x in sorted_langs]
    sizes = [x[1] for x in sorted_langs]
    colors = [lang_colors.get(l, "#cccccc") for l in labels]

    # Clean the matplotlib cache state completely 
    plt.clf()
    plt.close('all')
    plt.style.use('dark_background')
    
    # Create the figure with explicit dimensions
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), facecolor='#0a0a0a', gridspec_kw={'width_ratios': [1.2, 1]})
    
    # 🌟 FORCE COLUMN 1: Donut Chart Scale
    ax1.set_facecolor('#0a0a0a')
    ax1.axis('equal')  # Forces the pie chart to maintain a perfect square/circle shape
    
    wedges, texts, autotexts = ax1.pie(
        sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
        startangle=140, pctdistance=0.70, textprops=dict(color="#a9b1d6", weight="bold", fontsize=10)
    )

    centre_circle = plt.Circle((0,0), 0.50, fc='#0a0a0a')
    ax1.add_artist(centre_circle)
    ax1.set_title("Top Languages (Inc. Orgs & Forks)", color="#00FFCC", fontsize=12, weight="bold", pad=15)

    # 🌟 FORCE COLUMN 2: Text Layout Scale
    ax2.set_facecolor('#0a0a0a')
    ax2.axis('off') 
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)

    ax2.text(0.0, 0.85, "📊 Code Volume Breakdown", color="#00FFCC", fontsize=13, weight="bold")
    
    y_pos = 0.68
    for label, byte_size in sorted_langs:
        lines_of_code = int(byte_size / 35)
        loc_text = f"{lines_of_code:,} lines" if lines_of_code > 0 else f"{byte_size} bytes"
        
        # Draw explicit tiny markers using absolute layout coordinates
        ax2.scatter(0.05, y_pos + 0.03, color=lang_colors.get(label, "#cccccc"), marker='s', s=60)

        ax2.text(0.12, y_pos, f"{label}:", color="#ffffff", fontsize=11, weight="bold")
        ax2.text(0.52, y_pos, loc_text, color="#a9b1d6", fontsize=11)
        y_pos -= 0.12
        
    plt.tight_layout()
    
    os.makedirs("assets", exist_ok=True)
    plt.savefig("assets/custom-languages.png", dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')

if __name__ == "__main__":
    main()
