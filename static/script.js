// Selectors
const messages = document.getElementById("messages");
const chatbotToggle = document.getElementById("chatbot-toggle");
const chatbotClose = document.getElementById("chatbot-close");
const chatbotWindow = document.getElementById("chatbot-window");
const menuIcon = document.getElementById("menu-icon");
const navbar = document.querySelector(".navbar");
const navLinks = document.querySelectorAll(".navbar a");
const sections = document.querySelectorAll("section");

// 1. Chatbot Open/Close Toggle
chatbotToggle.addEventListener("click", () => {
    chatbotWindow.classList.toggle("active");
});

chatbotClose.addEventListener("click", () => {
    chatbotWindow.classList.remove("active");
});

// 2. Mobile Responsive Menu
menuIcon.addEventListener("click", () => {
    navbar.classList.toggle("active");
    menuIcon.querySelector("i").classList.toggle("fa-xmark");
});

// Close mobile menu when a link is clicked
navLinks.forEach(link => {
    link.addEventListener("click", () => {
        navbar.classList.remove("active");
        menuIcon.querySelector("i").classList.remove("fa-xmark");
        menuIcon.querySelector("i").classList.add("fa-bars");
    });
});

// 3. Scroll Section Active Navbar Link Highlight
window.addEventListener("scroll", () => {
    let top = window.scrollY;

    sections.forEach(sec => {
        let offset = sec.offsetTop - 150;
        let height = sec.offsetHeight;
        let id = sec.getAttribute("id");

        if (top >= offset && top < offset + height) {
            navLinks.forEach(links => {
                links.classList.remove("active");
                document.querySelector(".navbar a[href*=" + id + "]").classList.add("active");
            });
        }
    });
});

// 4. Rotating Typewriter Effect
const words = ["BS Metallurgical Engineer", "Virtual Assistant", "Researcher", "Academic Tutor"];
let wordIdx = 0;
let charIdx = 0;
let isDeleting = false;
const typingTextElement = document.querySelector(".typing-text");

function typeEffect() {
    const currentWord = words[wordIdx];
    
    if (isDeleting) {
        typingTextElement.textContent = currentWord.substring(0, charIdx - 1);
        charIdx--;
    } else {
        typingTextElement.textContent = currentWord.substring(0, charIdx + 1);
        charIdx++;
    }

    let typeSpeed = isDeleting ? 40 : 80;

    if (!isDeleting && charIdx === currentWord.length) {
        typeSpeed = 2000; // Pause at full word
        isDeleting = true;
    } else if (isDeleting && charIdx === 0) {
        isDeleting = false;
        wordIdx = (wordIdx + 1) % words.length;
        typeSpeed = 500; // Pause before typing next word
    }

    setTimeout(typeEffect, typeSpeed);
}

// Start Typewriter
if (typingTextElement) {
    typeEffect();
}

// 5. Chatbot Core Logic (Flask Fetch Integration)
function addMessage(text, cls) {
    const div = document.createElement("div");
    div.className = "message " + cls;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

async function loadHistory() {
    try {
        const response = await fetch("/history");
        const data = await response.json();
        messages.innerHTML = "";
        
        // Welcome message if history is empty
        if (!data.history || data.history.length === 0) {
            addMessage("Hi, I am Scepter, Vince's virtual assistant. Ask me anything about Vince's skills, education, or work experiences!", "bot");
            return;
        }
        
        data.history.forEach(msg => {
            const cls = msg.role === "user" ? "user" : "bot";
            addMessage(msg.content, cls);
        });
    } catch (e) {
        console.error("Failed to load history:", e);
    }
}

async function sendMessage() {
    const input = document.getElementById("message");
    const message = input.value.trim();
    if (message === "") return;

    addMessage(message, "user");
    input.value = "";

    // Show bouncing dot indicator
    const thinkingNode = addThinkingIndicator();

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();
        
        // Remove typing indicator and add response
        thinkingNode.innerHTML = "";
        thinkingNode.classList.remove("thinking-indicator");
        thinkingNode.textContent = data.response;
    } catch (e) {
        thinkingNode.innerHTML = "";
        thinkingNode.classList.remove("thinking-indicator");
        thinkingNode.textContent = "Server Not Available.";
    }

    messages.scrollTop = messages.scrollHeight;
}

function addThinkingIndicator() {
    const div = document.createElement("div");
    div.className = "message bot thinking-indicator";

    const container = document.createElement("div");
    container.className = "thinking-container";

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement("div");
        dot.className = "dot";
        container.appendChild(dot);
    }

    div.appendChild(container);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
}

async function resetChat() {
    try {
        await fetch("/reset", {
            method: "POST"
        });
        messages.innerHTML = "";
        addMessage("Nareset na ang chat history. Magtanong muli tungkol kay Vince!", "bot");
    } catch (e) {
        console.error("Failed to reset chat:", e);
    }
}

// Automatically load history on page load
window.addEventListener("DOMContentLoaded", loadHistory);

// Contact Form AJAX Submission
const contactForm = document.querySelector(".contact-form");
if (contactForm) {
    contactForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const submitBtn = contactForm.querySelector('input[type="submit"]');
        const originalBtnValue = submitBtn.value;
        submitBtn.value = "Sending...";
        submitBtn.disabled = true;
        
        const formData = new FormData(contactForm);
        const object = Object.fromEntries(formData);
        const json = JSON.stringify(object);
        
        try {
            const response = await fetch("https://api.web3forms.com/submit", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: json
            });
            const result = await response.json();
            if (response.status === 200) {
                alert("Mensahe ay matagumpay na naipadala!");
                contactForm.reset();
            } else {
                alert("May naganap na isyu: " + result.message);
            }
        } catch (error) {
            alert("Hindi maipadala ang mensahe. Pakisubukang muli mamaya.");
        } finally {
            submitBtn.value = originalBtnValue;
            submitBtn.disabled = false;
        }
    });
}