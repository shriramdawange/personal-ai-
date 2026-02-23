// The System Prompt: This shapes the AI's personality
const systemPrompt = "You are a calming, empathetic health assistant and meditation guide. Provide short, supportive, and practical advice to help the user manage stress and stay organized. Never provide medical diagnoses.";

// We are using a fast, capable model from Hugging Face
const modelEndpoint = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2";

async function sendMessage() {
    const userInput = document.getElementById('userInput').value;
    const apiKey = document.getElementById('apiKeyInput').value;
    const chatWindow = document.getElementById('chatWindow');

    if (!apiKey) {
        alert("Please enter your Hugging Face API key first!");
        return;
    }
    if (!userInput) return;

    // Display User Message
    chatWindow.innerHTML += `<div class="message user-msg">${userInput}</div>`;
    document.getElementById('userInput').value = '';

    // Format the prompt for the model (System Prompt + User Input)
    const formattedPrompt = `<s>[INST] ${systemPrompt} \n\n User: ${userInput} [/INST]`;

    try {
        const response = await fetch(modelEndpoint, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${apiKey}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                inputs: formattedPrompt,
                parameters: { max_new_tokens: 150, temperature: 0.7 }
            })
        });

        const data = await response.json();
        
        // Extracting the AI's reply and displaying it
        let aiReply = data[0].generated_text.replace(formattedPrompt, "").trim();
        chatWindow.innerHTML += `<div class="message ai-msg">${aiReply}</div>`;
        
        // Scroll to bottom
        chatWindow.scrollTop = chatWindow.scrollHeight;

    } catch (error) {
        chatWindow.innerHTML += `<div class="message ai-msg" style="color: red;">Error connecting to AI. Check your API key or internet connection.</div>`;
    }
}
