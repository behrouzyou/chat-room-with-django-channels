const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const messagesContainer = document.getElementById("messages");
const connectionStatus = document.getElementById("connectionStatus");
const onlineUsersContainer = document.getElementById("onlineUsers");
const onlineCount = document.getElementById("onlineCount");

let typingTimeout = null;
let isTyping = false;
const TYPING_STOP_DELAY = 2000;

function startTyping(){
    if (socket.readyState !== WebSocket.OPEN) {return;}

    if (!isTyping) {
        isTyping = true;
        socket.send(JSON.stringify({type:"typing_start"}));
    }

    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(stopTyping, TYPING_STOP_DELAY);
}

function stopTyping(){
    clearTimeout(typingTimeout);
    typingTimeout = null;

    if (!isTyping) {return;}

    isTyping = false;

    if (socket.readyState === WebSocket.OPEN) {socket.send(JSON.stringify({type:"typing_stop"}));}
}

const typingContainer = document.getElementById("typingIndicator");
typingContainer.style.display = "none";
typingContainer.textContent = "";

function showTypingUser(username) {
    typingContainer.textContent = username + " is typing...";
    typingContainer.style.display = "block";
}

function hideTypingUser(){
    typingContainer.textContent = "";
    typingContainer.style.display = "none";
}


function renderOnlineUsers(users) {
    onlineUsersContainer.innerHTML = "";
    onlineCount.textContent = users.length + " online";

    users.forEach(function(user) {
        const userElement = document.createElement("div");
        userElement.classList.add("online-user");

        const dot = document.createElement("span");
        dot.classList.add("online-dot");

        const username = document.createElement("span");
        username.textContent = user.username;

        userElement.appendChild(dot);
        userElement.appendChild(username);

        onlineUsersContainer.appendChild(userElement);
    });
}

function formatTime(timestamp){
    if (!timestamp) {return "";}
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"});
}

function addMessage(message){
    const messageElement = document.createElement("div");
    const isOwnMessage = message.username === currentUsername;
    messageElement.classList.add("message");

    if (isOwnMessage){
        messageElement.classList.add("message-own");
    } else {
        messageElement.classList.add("message-other");
    }

    const usernameElement = document.createElement("div");
    usernameElement.classList.add("message-username");
    usernameElement.textContent = message.username;

    const contentElement = document.createElement("div");
    contentElement.classList.add("message-content");
    contentElement.textContent = message.message;

    const timeElement = document.createElement("div");
    timeElement.classList.add("message-time");
    timeElement.textContent = formatTime(message.created_at);

    messageElement.appendChild(usernameElement);
    messageElement.appendChild(contentElement);
    messageElement.appendChild(timeElement);

    messagesContainer.appendChild(messageElement);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addSystemMessage(text){
    const element = document.createElement("div");
    element.classList.add("system-message");
    element.textContent = text;
    messagesContainer.appendChild(element);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showError(text) {
    const element = document.createElement("div");
    element.classList.add("error-message");
    element.textContent = text;
    messagesContainer.appendChild(element);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

socket.onopen = function() {
    console.log("Websocket connected");
    connectionStatus.textContent = "Connected";
    connectionStatus.className = "status-online";
    sendButton.disabled = false;
    messageInput.focus();
};

socket.onmessage = function(event) {
    let data;

    try {
        data = JSON.parse(event.data);
    } catch (error) {
        console.error("Invalid server response: ", event.data);
        return
    }

    if (data.reason === "history") {
        messagesContainer.innerHTML = "";
        data.messages.forEach(function(message){
            addMessage(message);
        });

        renderOnlineUsers(data.online_users || []);

        return;
    }

    if (data.reason === "message"){
        addMessage({
            id: data.id,
            message: data.message,
            username: data.username,
            user_id: data.user_id,
            created_at: data.created_at
        });
        return;
    }

    if (data.reason === "user_joined"){
        if (data.username !== currentUsername){
            addSystemMessage(data.username + " joined the room");
        }

        const existingUsers = Array.from(onlineUsersContainer
            .querySelectorAll(".online-user span:last-child")).map(function(element){
                return element.textContent;
            });

        if (!existingUsers.includes(data.username)) {
            const userElement = document.createElement("div");
            userElement.classList.add("online-user");

            const dot = document.createElement("span");
            dot.classList.add("online-dot");

            const username = document.createElement("span");
            username.textContent = data.username;

            userElement.appendChild(dot);
            userElement.appendChild(username);
            onlineUsersContainer.appendChild(userElement);

            onlineCount.textContent = onlineUsersContainer.querySelectorAll(".online-user").length + " online";
        }

        return;
    }

    if (data.reason === "user_left"){
        addSystemMessage(data.username + " left the room");

        const users = onlineUsersContainer.querySelectorAll(".online-user");
        users.forEach(function(userElement) {
            const username = userElement.querySelector("span:last-child").textContent;
            if(username === data.username) {userElement.remove()}
        });

        onlineCount.textContent = onlineUsersContainer.querySelectorAll(".online-user").length + " online";
        hideTypingUser();
        return;
    }

    if (data.reason === "typing"){
        if(data.username === currentUsername) {return;}
        if (data.action === "start") {showTypingUser(data.username);}
        if (data.action === "stop") {hideTypingUser();}
        return;
    }

    if (data.reason === "error") {
        showError(data.message);
        return;
    }

};
socket.onclose = function() {
    console.log("WebSocket disconnected");
    connectionStatus.textContent = "Disconnected";
    connectionStatus.className = "status-offline";
    sendButton.disabled = true;
};

socket.onerror = function(error){
    console.error("Websocket error: ", error);
};

function sendMessage(){
    const message = messageInput.value.trim();
    if (!message){
        return;
    }

    if (socket.readyState !== WebSocket.OPEN) {
        showError("Connection is not available.");
        return;
    }
    stopTyping()
    socket.send(JSON.stringify({message:message}))
    messageInput.value = "";
    messageInput.focus();
}

sendButton.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", function(event){
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

messageInput.addEventListener("input", function(){
    if (messageInput.value.trim() === ""){
        stopTyping();
        return;
    }
    startTyping();
});