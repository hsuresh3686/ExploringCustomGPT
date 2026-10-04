# ExploringCustomGPT
Exploring the Custom GPT in simple and various ways
Steps:

1. Created API Key in OpenAI
2. Set the API Key in the System Environment Variables by using below command

   1. Open Command Prompt
   2. Run setx OPENAI_API_KEY "YOUR_OPENAI_API_KEY"
   
4. We can use the API Key in our code by calling

   1. from openai import OpenAI
   2. client = OpenAI() 
