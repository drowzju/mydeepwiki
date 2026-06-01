#!/usr/bin/env python3
"""
DeepWiki CLI Builder - Command line client for generating wiki without browser
Usage: python wiki_builder.py <repo_url> [options]
"""

import argparse
import asyncio
import json
import os
import sys
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import websockets
import aiohttp
from datetime import datetime
import time


class WikiBuilder:
    """CLI client for building wiki from command line"""

    def __init__(self, server_url: str = "ws://localhost:8091"):
        self.server_url = server_url
        self.ws_url = server_url.replace("http://", "ws://").replace("https://", "wss://")
        self.http_url = server_url.replace("ws://", "http://").replace("wss://", "https://")
        self.generated_pages: Dict[str, Any] = {}
        self.wiki_structure: Optional[Dict] = None
        self.start_time: Optional[float] = None

    def _print_progress_bar(self, current: int, total: int, prefix: str = "", suffix: str = "", length: int = 40):
        """Print a progress bar"""
        filled = int(length * current // total)
        bar = "█" * filled + "░" * (length - filled)
        percent = 100 * current // total
        print(f"\r{prefix} |{bar}| {percent}% {suffix}", end="", flush=True)
        if current == total:
            print()

    def _format_time(self, seconds: float) -> str:
        """Format seconds to human readable time"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"

    async def send_websocket_request(
        self,
        request_body: Dict,
        on_progress: Optional[callable] = None,
        page_title: str = "",
        current_page: int = 0,
        total_pages: int = 0
    ) -> str:
        """Send request via WebSocket and collect response with progress"""
        ws_endpoint = f"{self.ws_url}/ws/chat"

        if not page_title:
            print(f"Connecting to {ws_endpoint}...")

        response_text = ""
        char_count = 0
        last_update = time.time()

        try:
            async with websockets.connect(ws_endpoint, ping_interval=None) as ws:
                await ws.send(json.dumps(request_body))

                async for message in ws:
                    response_text += message
                    char_count += len(message)

                    # Update progress every 0.5 seconds
                    now = time.time()
                    if now - last_update > 0.5:
                        if on_progress:
                            on_progress(char_count)
                        elif page_title:
                            print(f"\r  Generating {page_title}... ({char_count} chars received)", end="", flush=True)
                        last_update = now

        except Exception as e:
            if page_title:
                print()
            print(f"WebSocket error: {e}")
            return await self.send_http_request(request_body)

        if page_title:
            print()
        return response_text

    async def send_http_request(self, request_body: Dict) -> str:
        """Fallback HTTP request"""
        http_endpoint = f"{self.http_url}/chat/completions/stream"
        print(f"Using HTTP fallback: {http_endpoint}")

        async with aiohttp.ClientSession() as session:
            async with session.post(http_endpoint, json=request_body) as response:
                text = await response.text()
                return text

    async def generate_wiki_structure(
        self,
        repo_url: str,
        repo_type: str = "github",
        token: Optional[str] = None,
        provider: str = "google",
        model: str = "gemini-2.5-flash",
        language: str = "en",
        is_comprehensive: bool = False,
        excluded_dirs: str = "",
        excluded_files: str = ""
    ) -> Optional[Dict]:
        """Generate wiki structure (list of pages)"""

        prompt = self._get_structure_prompt(repo_url, repo_type, is_comprehensive)

        request_body = {
            "repo_url": repo_url,
            "type": repo_type,
            "provider": provider,
            "model": model,
            "language": language,
            "messages": [{"role": "user", "content": prompt}]
        }

        if token:
            request_body["token"] = token
        if excluded_dirs:
            request_body["excluded_dirs"] = excluded_dirs
        if excluded_files:
            request_body["excluded_files"] = excluded_files

        print("\n" + "=" * 60)
        print("STEP 1: Generating wiki structure...")
        print("=" * 60)

        response = await self.send_websocket_request(request_body)

        # Clean up response
        response = response.replace("```xml", "").replace("```", "").strip()

        # Parse XML
        try:
            xml_match = response[response.find("<wiki_structure>"):response.find("</wiki_structure>") + 17]
            root = ET.fromstring(xml_match)

            wiki_structure = {
                "id": root.get("id", "wiki"),
                "title": root.findtext("title", ""),
                "description": root.findtext("description", ""),
                "pages": []
            }

            for page_elem in root.findall(".//page"):
                page = {
                    "id": page_elem.get("id", ""),
                    "title": page_elem.findtext("title", ""),
                    "description": page_elem.findtext("description", ""),
                    "importance": page_elem.findtext("importance", "medium"),
                    "filePaths": [],
                    "relatedPages": []
                }

                # Get file paths
                files_elem = page_elem.find("relevant_files")
                if files_elem:
                    page["filePaths"] = [f.text for f in files_elem.findall("file_path") if f.text]

                # Get related pages
                related_elem = page_elem.find("related_pages")
                if related_elem:
                    page["relatedPages"] = [r.text for r in related_elem.findall("related") if r.text]

                wiki_structure["pages"].append(page)

            self.wiki_structure = wiki_structure
            print(f"\n✓ Generated wiki structure with {len(wiki_structure['pages'])} pages")
            for i, page in enumerate(wiki_structure["pages"], 1):
                importance_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(page["importance"], "⚪")
                print(f"  {i}. {importance_emoji} {page['title']} ({page['importance']})")

            return wiki_structure

        except Exception as e:
            print(f"\n✗ Error parsing wiki structure: {e}")
            print(f"Raw response:\n{response[:500]}...")
            return None

    async def generate_page_content(
        self,
        page: Dict,
        repo_url: str,
        repo_type: str = "github",
        token: Optional[str] = None,
        provider: str = "google",
        model: str = "gemini-2.5-flash",
        language: str = "en",
        excluded_dirs: str = "",
        excluded_files: str = ""
    ) -> str:
        """Generate content for a single page"""

        prompt = self._get_page_prompt(page, repo_url, repo_type, language)

        request_body = {
            "repo_url": repo_url,
            "type": repo_type,
            "provider": provider,
            "model": model,
            "language": language,
            "messages": [{"role": "user", "content": prompt}]
        }

        if token:
            request_body["token"] = token
        if page.get("filePaths"):
            request_body["filePath"] = page["filePaths"][0]
        if excluded_dirs:
            request_body["excluded_dirs"] = excluded_dirs
        if excluded_files:
            request_body["excluded_files"] = excluded_files

        response = await self.send_websocket_request(
            request_body,
            page_title=page["title"]
        )

        # Clean up markdown delimiters
        content = response.replace("```markdown", "").replace("```", "").strip()
        return content

    async def generate_all_pages(
        self,
        wiki_structure: Dict,
        repo_url: str,
        repo_type: str = "github",
        token: Optional[str] = None,
        provider: str = "google",
        model: str = "gemini-2.5-flash",
        language: str = "en",
        excluded_dirs: str = "",
        excluded_files: str = ""
    ) -> Dict[str, Any]:
        """Generate content for all pages with progress"""

        print("\n" + "=" * 70)
        print("STEP 2: Generating page contents...")
        print("=" * 70)

        total = len(wiki_structure["pages"])
        generated_pages = {}
        self.start_time = time.time()

        # Group by importance for better visualization
        pages_by_importance = {"high": [], "medium": [], "low": []}
        for page in wiki_structure["pages"]:
            pages_by_importance.get(page["importance"], []).append(page)

        print(f"\n📋 Total pages to generate: {total}")
        print(f"   🔴 High: {len(pages_by_importance['high'])}")
        print(f"   🟡 Medium: {len(pages_by_importance['medium'])}")
        print(f"   🟢 Low: {len(pages_by_importance['low'])}\n")

        for i, page in enumerate(wiki_structure["pages"], 1):
            importance_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(page["importance"], "⚪")

            # Show progress bar
            elapsed = time.time() - self.start_time
            avg_time_per_page = elapsed / (i - 1) if i > 1 else 0
            remaining_pages = total - i + 1
            estimated_remaining = avg_time_per_page * remaining_pages

            print(f"\n[{i}/{total}] {importance_emoji} {page['title']}")
            self._print_progress_bar(i-1, total, prefix="Overall",
                suffix=f"ETA: {self._format_time(estimated_remaining)}")

            page_start = time.time()

            try:
                content = await self.generate_page_content(
                    page, repo_url, repo_type, token,
                    provider, model, language,
                    excluded_dirs, excluded_files
                )

                generated_pages[page["id"]] = {
                    **page,
                    "content": content
                }

                page_time = time.time() - page_start
                print(f"  ✓ Completed in {self._format_time(page_time)} ({len(content)} chars)")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                generated_pages[page["id"]] = {
                    **page,
                    "content": f"Error generating content: {e}"
                }

        # Final progress
        total_time = time.time() - self.start_time
        print(f"\n{'=' * 70}")
        print(f"✓ All pages generated in {self._format_time(total_time)}")
        print(f"{'=' * 70}")

        self.generated_pages = generated_pages
        return generated_pages

    async def save_wiki_cache(
        self,
        repo_owner: str,
        repo_name: str,
        repo_type: str,
        language: str,
        provider: str,
        model: str
    ) -> bool:
        """Save generated wiki to server cache"""

        if not self.wiki_structure or not self.generated_pages:
            print("No wiki data to save")
            return False

        cache_data = {
            "repo": {
                "owner": repo_owner,
                "repo": repo_name,
                "type": repo_type,
                "token": None,
                "localPath": None,
                "repoUrl": f"https://{repo_type}.com/{repo_owner}/{repo_name}"
            },
            "language": language,
            "wiki_structure": self.wiki_structure,
            "generated_pages": self.generated_pages,
            "provider": provider,
            "model": model
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.http_url}/api/wiki_cache",
                    json=cache_data
                ) as response:
                    if response.status == 200:
                        print("\n✓ Wiki saved to server cache successfully")
                        return True
                    else:
                        error = await response.text()
                        print(f"\n✗ Failed to save wiki: {error}")
                        return False
        except Exception as e:
            print(f"\n✗ Error saving wiki: {e}")
            return False

    def export_wiki(self, repo_url: str, output_dir: str = ".") -> str:
        """Export wiki to local markdown file"""

        if not self.wiki_structure or not self.generated_pages:
            return "No wiki data to export"

        repo_name = repo_url.split("/")[-1] if "/" in repo_url else "wiki"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{repo_name}_wiki_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        markdown = f"# {self.wiki_structure['title']}\n\n"
        markdown += f"{self.wiki_structure['description']}\n\n"
        markdown += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        markdown += "---\n\n"

        # Table of contents
        markdown += "## Table of Contents\n\n"
        for page_id, page in self.generated_pages.items():
            markdown += f"- [{page['title']}](#{page_id})\n"
        markdown += "\n---\n\n"

        # Page contents
        for page_id, page in self.generated_pages.items():
            markdown += f"<a id='{page_id}'></a>\n\n"
            markdown += f"## {page['title']}\n\n"
            markdown += f"{page['content']}\n\n"
            markdown += "---\n\n"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return filepath

    def _get_structure_prompt(self, repo_url: str, repo_type: str, is_comprehensive: bool) -> str:
        """Generate prompt for wiki structure"""
        return f'''Analyze this {repo_type} repository: {repo_url}

Create a comprehensive wiki structure that explains this codebase to developers.

Return your response as a valid XML structure following this exact format:

<wiki_structure id="wiki">
  <title>[Overall title for the wiki]</title>
  <description>[Brief description of the repository]</description>
  <pages>
    <page id="page-1">
      <title>[Page title]</title>
      <description>[Brief description of what this page will cover]</description>
      <importance>high|medium|low</importance>
      <relevant_files>
        <file_path>[Path to a relevant file]</file_path>
      </relevant_files>
      <related_pages>
        <related>page-2</related>
      </related_pages>
    </page>
  </pages>
</wiki_structure>

Create {"8-12" if is_comprehensive else "4-6"} pages that would make a {"comprehensive" if is_comprehensive else "concise"} wiki.
Return ONLY valid XML with no markdown code blocks.'''

    def _get_page_prompt(self, page: Dict, repo_url: str, repo_type: str, language: str) -> str:
        """Generate prompt for page content"""
        lang_names = {
            "en": "English", "zh": "Chinese", "ja": "Japanese",
            "es": "Spanish", "kr": "Korean", "vi": "Vietnamese",
            "fr": "French", "ru": "Russian", "pt-br": "Portuguese"
        }
        lang_name = lang_names.get(language, "English")

        return f'''Write a comprehensive wiki page about "{page['title']}" for the repository: {repo_url}

This page should cover: {page['description']}

You MUST respond in {lang_name} language.

Write detailed documentation including:
- Overview of the topic
- Key concepts and explanations
- Code examples where relevant
- Best practices

Use proper markdown formatting with headers, lists, and code blocks.'''


async def main():
    parser = argparse.ArgumentParser(
        description="DeepWiki CLI Builder - Generate wiki from command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wiki_builder.py owner/repo
  python wiki_builder.py https://github.com/owner/repo --provider openai --model gpt-4
  python wiki_builder.py /path/to/local/repo --type local --language zh
        """
    )

    parser.add_argument("repo", help="Repository URL, owner/repo format, or local path")
    parser.add_argument("--type", default="github",
                       choices=["github", "gitlab", "bitbucket", "local"],
                       help="Repository type (default: github)")
    parser.add_argument("--token", help="Personal access token for private repos")
    parser.add_argument("--provider", default="google",
                       help="Model provider (default: google)")
    parser.add_argument("--model", default="gemini-2.5-flash",
                       help="Model name (default: gemini-2.5-flash)")
    parser.add_argument("--language", default="en",
                       choices=["en", "zh", "ja", "es", "kr", "vi", "fr", "ru", "pt-br", "zh-tw"],
                       help="Wiki language (default: en)")
    parser.add_argument("--server", default="ws://localhost:8091",
                       help="WebSocket server URL (default: ws://localhost:8091)")
    parser.add_argument("--comprehensive", action="store_true",
                       help="Generate comprehensive wiki with more pages")
    parser.add_argument("--output", "-o", default=".",
                       help="Output directory for exported markdown (default: current)")
    parser.add_argument("--excluded-dirs", default="",
                       help="Comma-separated list of directories to exclude")
    parser.add_argument("--excluded-files", default="",
                       help="Comma-separated list of file patterns to exclude")
    parser.add_argument("--no-cache", action="store_true",
                       help="Don't save to server cache")

    args = parser.parse_args()

    # Parse repo URL
    repo_url = args.repo
    if "/" in args.repo and not args.repo.startswith("http") and not args.repo.startswith("/"):
        # owner/repo format
        repo_url = f"https://github.com/{args.repo}"
        args.type = "github"

    owner = repo_url.split("/")[-2] if "/" in repo_url else "local"
    repo_name = repo_url.split("/")[-1] if "/" in repo_url else os.path.basename(repo_url)

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    DeepWiki CLI Builder v1.0                         ║
╠══════════════════════════════════════════════════════════════════════╣
║  Repository: {repo_url[:50]:<50} ║
║  Type:      {args.type:<10}  Provider: {args.provider:<15}              ║
║  Model:     {args.model:<25}  Language: {args.language:<10}             ║
║  Output:    {args.output:<50}  ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Create builder
    builder = WikiBuilder(server_url=args.server)

    # Generate wiki structure
    wiki_structure = await builder.generate_wiki_structure(
        repo_url=repo_url,
        repo_type=args.type,
        token=args.token,
        provider=args.provider,
        model=args.model,
        language=args.language,
        is_comprehensive=args.comprehensive,
        excluded_dirs=args.excluded_dirs,
        excluded_files=args.excluded_files
    )

    if not wiki_structure:
        print("\n✗ Failed to generate wiki structure")
        sys.exit(1)

    # Generate all pages
    generated_pages = await builder.generate_all_pages(
        wiki_structure=wiki_structure,
        repo_url=repo_url,
        repo_type=args.type,
        token=args.token,
        provider=args.provider,
        model=args.model,
        language=args.language,
        excluded_dirs=args.excluded_dirs,
        excluded_files=args.excluded_files
    )

    # Save to server cache
    if not args.no_cache:
        await builder.save_wiki_cache(
            repo_owner=owner,
            repo_name=repo_name,
            repo_type=args.type,
            language=args.language,
            provider=args.provider,
            model=args.model
        )

    # Export to local file
    output_path = builder.export_wiki(repo_url, args.output)
    print(f"\n✓ Wiki exported to: {output_path}")

    print("\n" + "=" * 70)
    print("                    🎉 Wiki generation complete! 🎉")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
