document.addEventListener("DOMContentLoaded", function () {
    const chatbox = document.getElementById("chatbox");
    const userinput = document.getElementById("userinput");
    const sendbtn = document.getElementById("sendbtn");

    // Initial loading of historical chat records
    loadChatHistory();

    sendbtn.addEventListener("click", sendMessage);

    // Monitor keyboard enter events
    userinput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    function sendMessage() {
        const userMessage = userinput.value.trim();
        if (userMessage) {
            // Display user messages and save to database
            displayMessage("User: " + userMessage, "user");
            userinput.value = "";

            // Send message to the backend
            fetch('/send_message', {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage })
            })
                .then(response => response.json())
                .then(data => {
                    const reply = data.reply || "Sorry, I didn't understand that.";
                    displayMessage("Assistance: " + reply, "assistant");
                    displayDivider();
                })
                .catch(error => {
                    console.error("Error fetching response:", error);
                    const errorMessage = "Assistance: Error fetching response, please try again later.";
                    displayMessage(errorMessage, "assistant");
                    saveMessageToServer(errorMessage, "Assistance");
                });
        }
    }

    function loadChatHistory() {
        fetch("/get_history")
            .then((response) => response.json())
            .then((data) => {
                const history = data.history;

                // If the history is empty, show a welcome message
                if (history.length === 0) {
                    const welcomeMessage = "Welcome to Laptop Online Assistant. Please state the product name you would like to learn about to obtain the support resources you need or chat with our technicians.<br>Pick One: <br>1. look for specific laptop<br>2. normal issue";
                    saveMessageToServer(welcomeMessage, "Assistance");
                    displayMessage(welcomeMessage, "assistant");
                    displayDivider();
                } else {
                    // Display history messages
                    history.forEach((msg) => {
                        const sender = msg.sender === "User" ? "user" : "assistant";
                        displayMessage(`${msg.sender}: ${msg.message}`, sender);
                        displayDivider();
                    });
                }
            })
            .catch((error) => {
                console.error("Error loading chat history:", error);
                const errorMessage = "Assistance: Error loading chat history, please try again later.";
                saveMessageToServer(errorMessage, "Assistance");
                displayMessage(errorMessage, "assistant");
            });
    }

    function displayMessage(content, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}`;
        
        // Convert \n to <br> tags for proper line breaking in HTML
        const formattedContent = content.replace(/\n/g, "<br>");
        messageDiv.innerHTML = formattedContent;

        chatbox.appendChild(messageDiv);
        chatbox.scrollTop = chatbox.scrollHeight; // Scroll to bottom
    }

    function displayDivider() {
        const divider = document.createElement("hr");
        divider.className = "divider";
        chatbox.appendChild(divider);
    }

    function saveMessageToServer(content, sender) {
        fetch("/store_message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: content, sender: sender })
        })
            .then(response => response.json())
            .then(data => {
                console.log("Message saved:", data);
            })
            .catch(error => {
                console.error("Error saving message:", error);
            });
    }
});
