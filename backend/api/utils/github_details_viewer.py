from ..extractors.details_extractor import DetailsExtractor

def get_github_details(github_url):
    """
    Get GitHub details using the existing details extractor
    """
    try:
        extractor = DetailsExtractor()
        # The extract_github_details method expects text, but we can pass the URL directly
        # since the crawler will extract the username from it
        details = extractor.extract_github_details(github_url)
        return details
    except Exception as e:
        print(f"Error extracting GitHub details: {str(e)}")
        return None
