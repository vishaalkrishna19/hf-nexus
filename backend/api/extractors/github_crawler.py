import requests
import re

class GithubCrawler:
    def __init__(self, github_url):
        self.github_url = github_url
        self.username = self.extract_username(github_url)
        self.api_base = f"https://api.github.com/users/{self.username}"

    def extract_username(self, url):
        url = url.strip()
        if not url.startswith('http'):
            url = 'https://' + url
        match = re.search(r"github\.com/([\w.-]+)", url)
        return match.group(1) if match else None

    def get_profile_data(self):
        if not self.username:
            print(f"No username extracted from URL: {self.github_url}")
            return None
            
        print(f"Fetching GitHub data for username: {self.username}")
        
        try:
            user_resp = requests.get(self.api_base, timeout=10)
            if user_resp.status_code != 200:
                print(f"GitHub API error for user: {user_resp.status_code}")
                return None

            user_data = user_resp.json()
            
            repos_resp = requests.get(f"{self.api_base}/repos?per_page=100&sort=updated", timeout=10)
            repos_data = repos_resp.json() if repos_resp.status_code == 200 else []

            languages_stats = self._calculate_language_stats(repos_data)
            total_commits = self._calculate_total_commits(repos_data[:20])

            result = {
                "username": user_data.get("login"),
                "name": user_data.get("name"),
                "bio": user_data.get("bio"),
                "location": user_data.get("location"),
                "avatar_url": user_data.get("avatar_url"),
                "html_url": user_data.get("html_url"),
                "public_repos": user_data.get("public_repos", 0),
                "followers": user_data.get("followers", 0),
                "following": user_data.get("following", 0),
                "created_at": user_data.get("created_at"),
                "updated_at": user_data.get("updated_at"),
                "most_used_languages": languages_stats,
                "total_commits": total_commits,
            }
            
            if repos_data:
                sorted_repos = sorted(repos_data, key=lambda x: x.get("stargazers_count", 0), reverse=True)
                result["top_repos"] = []
                for repo in sorted_repos[:5]:
                    result["top_repos"].append({
                        "name": repo.get("name"),
                        "description": repo.get("description"),
                        "html_url": repo.get("html_url"),
                        "stargazers_count": repo.get("stargazers_count", 0),
                        "language": repo.get("language"),
                        "forks_count": repo.get("forks_count", 0)
                    })
            
            print(f"Successfully fetched GitHub data: {result}")
            return result
            
        except requests.RequestException as e:
            print(f"Request error fetching GitHub data: {str(e)}")
            return None
        except Exception as e:
            print(f"Error fetching GitHub data: {str(e)}")
            return None

    def _calculate_language_stats(self, repos_data):
        language_counts = {}
        total_repos = 0
        
        for repo in repos_data:
            if not repo.get("fork", False):
                language = repo.get("language")
                if language:
                    language_counts[language] = language_counts.get(language, 0) + 1
                    total_repos += 1
        
        language_stats = []
        for language, count in language_counts.items():
            percentage = round((count / total_repos) * 100, 1) if total_repos > 0 else 0
            language_stats.append({
                "language": language,
                "count": count,
                "percentage": percentage
            })
        
        language_stats.sort(key=lambda x: x["count"], reverse=True)
        
        return language_stats[:5]

    def _calculate_total_commits(self, repos_data):
        total_commits = 0
        
        for repo in repos_data:
            if not repo.get("fork", False):
                try:
                    commits_url = f"https://api.github.com/repos/{self.username}/{repo['name']}/commits"
                    commits_resp = requests.get(f"{commits_url}?per_page=1", timeout=5)
                    
                    if commits_resp.status_code == 200:
                        link_header = commits_resp.headers.get('link', '')
                        if 'rel="last"' in link_header:
                            import re
                            last_page_match = re.search(r'page=(\d+)>; rel="last"', link_header)
                            if last_page_match:
                                total_commits += int(last_page_match.group(1))
                        else:
                            commits_count_resp = requests.get(f"{commits_url}?per_page=100", timeout=5)
                            if commits_count_resp.status_code == 200:
                                total_commits += len(commits_count_resp.json())
                
                except Exception as e:
                    print(f"Error fetching commits for {repo['name']}: {str(e)}")
                    continue
        
        return total_commits
