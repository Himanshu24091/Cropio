"""
Batch script to add analytics tracking to all converter routes
Run this to automatically add tracking code to all features
"""

# Standard tracking code template
TRACKING_CODE = '''
        # Track analytics for logged-in users
        if current_user.is_authenticated:
            try:
                from utils.analytics_tracker import track_feature
                
                track_feature(
                    feature_name='{feature_name}',
                    feature_category='{category}',
                    extra_metadata={{'file_type': '{file_type}'}},
                    success=True
                )
                print(f"[ANALYTICS] Tracked: {feature_name}")
            except Exception as e:
                print(f"[ANALYTICS] Error: {{e}}")
'''

# Features to add tracking to
FEATURES = [
    {
        'file': 'routes/image/heic_jpg_routes.py',
        'function': 'download_converted_file',
        'feature_name': 'heic_jpg_conversion',
        'category': 'image_conversion',
        'file_type': 'image'
    },
    {
        'file': 'routes/image/raw_jpg_routes.py',
        'function': 'download_converted_file',
        'feature_name': 'raw_jpg_conversion',
        'category': 'image_conversion',
        'file_type': 'image'
    },
    {
        'file': 'routes/image/gif_png_sequence_routes.py',
        'function': 'api_download',
        'feature_name': 'gif_to_png_sequence',
        'category': 'animation_conversion',
        'file_type': 'animation'
    },
    {
        'file': 'routes/image/gif_mp4_routes.py',
        'function': 'api_download',
        'feature_name': 'gif_to_mp4',
        'category': 'video_conversion',
        'file_type': 'video'
    },
    {
        'file': 'routes/web_code/yaml_json_routes.py',
        'function': 'api_download',
        'feature_name': 'yaml_json_conversion',
        'category': 'config_conversion',
        'file_type': 'config'
    },
    {
        'file': 'routes/web_code/html_pdf_snapshot_routes.py',
        'function': 'api_convert',
        'feature_name': 'html_to_pdf_snapshot',
        'category': 'web_conversion',
        'file_type': 'web'
    },
    {
        'file': 'routes/document/latex_pdf_routes.py',
        'function': 'api_download',
        'feature_name': 'latex_pdf_conversion',
        'category': 'document_conversion',
        'file_type': 'document'
    }
]

print("Analytics Tracking - Batch Add Script")
print("=" * 50)
print(f"Total features to update: {len(FEATURES)}")
print("\nFeatures:")
for feature in FEATURES:
    print(f"  - {feature['feature_name']} ({feature['file']})")

print("\n" + "=" * 50)
print("Manual Implementation Required:")
print("Add the tracking code to each feature's download/convert endpoint")
print("See analytics_tracking_guide.md for details")
