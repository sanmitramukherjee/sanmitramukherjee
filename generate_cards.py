import os
import requests
import matplotlib.pyplot as plt
from collections import defaultdict

TOKEN = os.getenv("GH_TOKEN")
USERNAME = "sanmitramukherjee"

if not TOKEN:
    raise ValueError("GH_TOKEN secret is missing!")

# GraphQL Query targets owner repositories, organization memberships, and external collaborations
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
    
    for repo in repos:
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

    # Theme Styling (Matches Tokyo Night Theme / #0a0a0a Background)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(6, 4.5), facecolor='#0a0a0a')
    ax.set_facecolor('#0a0a0a')
    
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
        startangle=140, pctdistance=0.75, textprops=dict(color="#a9b1d6", weight="bold")
    )
    
    # Render inside hole to convert it to a modern Donut Chart
    centre_circle = plt.Circle((0,0), 0.50, fc='#0a0a0a')
    fig.gca().add_artist(centre_circle)
    
    plt.title("Top Languages (Inc. Orgs & Forks)", color="#00FFCC", fontsize=14, weight="bold", pad=20)
    plt.tight_layout()
    
    os.makedirs("assets", exist_ok=True)
    plt.savefig("assets/custom-languages.png", dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')

if __name__ == "__main__":
    main()
