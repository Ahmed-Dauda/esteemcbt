import openai
# Use your API key to authenticate with the API
openai.api_key = "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"
# Use the `create_image` function to generate an image based on a textual description
response = openai.Image.create(
	prompt="Freeform ferrofluids, beautiful dark chaos, swirling black frequency --ar 3:4 --iw 9 --q 2 --s 1250",
	n=1
)
# print(response)
# Save the image file to disk
image_url = response["data"][0]["url"]
print(image_url)
# Extract the image URL from the API response
image_url = response["data"][0]["url"]

# Step 4: Working with Image Responses



