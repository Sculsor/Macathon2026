print("Available models that support generateContent:")
for m in client.models.list():
    # Only print models that support generateContent
    if "generateContent" in m.supported_actions:
        print(" ", m.name)
