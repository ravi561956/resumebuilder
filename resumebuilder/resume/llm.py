from google import genai

client = genai.Client(api_key='AIzaSyDra00rsZgcBULSfjgt2qMB2s6fXFvu_aQ')

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="How does AI work?"
)
print(response.text)