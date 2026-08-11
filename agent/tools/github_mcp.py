import os
import requests
from dotenv import load_dotenv
from github import Github, GithubException, Auth
from mcp.server.fastmcp import FastMCP
import warnings

warnings.filterwarnings("ignore", module="pydantic_settings")


load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "ajiteshreddy24/microservices-demo")

mcp = FastMCP("GitHub-MCP-Server")

@mcp.tool()
def get_recent_deploys(service_name: str, limit: int = 5) -> dict:
    """
    Fetch recent commit and deployment history for a microservice from GitHub.
    Used by the agent to correlate anomalies with recent code deployments.
    
    Args:
        service_name: Name of the microservice (e.g., 'paymentservice')
        limit: Max number of recent commits to retrieve (default: 5)
        
    Returns:
        dict containing commit hash, author, timestamp, message, and URL.
    """
    try:
        commits_data = []
        
        # Method 1: Use PyGithub SDK if GITHUB_TOKEN is present
        if GITHUB_TOKEN:
            g = Github(auth=Auth.Token(GITHUB_TOKEN))
            repo = g.get_repo(GITHUB_REPO)
            
            # Fetch recent commits from repo
            commits = repo.get_commits()[:limit]
            
            for commit in commits:
                commits_data.append({
                    "sha": commit.sha[:7],
                    "full_sha": commit.sha,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.isoformat(),
                    "message": commit.commit.message.split("\n")[0],  # First line only
                    "url": commit.html_url
                })
        else:
            # Method 2: Public GitHub REST API fallback (unauthenticated)
            headers = {"Accept": "application/vnd.github.v3+json"}
            url = f"https://api.github.com/repos/{GITHUB_REPO}/commits?per_page={limit}"
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            raw_commits = response.json()
            for item in raw_commits:
                commits_data.append({
                    "sha": item["sha"][:7],
                    "full_sha": item["sha"],
                    "author": item["commit"]["author"]["name"],
                    "date": item["commit"]["author"]["date"],
                    "message": item["commit"]["message"].split("\n")[0],
                    "url": item["html_url"]
                })
                
        return {
            "status": "success",
            "repo": GITHUB_REPO,
            "service": service_name,
            "count": len(commits_data),
            "commits": commits_data
        }
        
    except GithubException as e:
        return {
            "status": "error",
            "service": service_name,
            "error": f"GitHub API SDK error: {e.data.get('message', str(e))}",
            "commits": []
        }
    except Exception as e:
        return {
            "status": "error",
            "service": service_name,
            "error": f"Failed to fetch GitHub commits: {str(e)}",
            "commits": []
        }

if __name__ == "__main__":
    print("Testing GitHub MCP tool locally...")
    test_result = get_recent_deploys(service_name="paymentservice", limit=3)
    print(f"Status: {test_result['status']}")
    if test_result['status'] == "error":
        print(f"Error: {test_result.get('error')}")
    else:
        print(f"Commits fetched: {test_result.get('count', 0)}")
        if test_result.get('commits'):
            c = test_result['commits'][0]
            print(f"Latest commit: [{c['sha']}] '{c['message']}' by {c['author']}")