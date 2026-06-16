// Function called from Python via pywebview
function update_status(mainText, subText, isListening) {
    document.getElementById('status-text').innerText = mainText;
    document.getElementById('sub-text').innerText = subText;
    
    if (isListening) {
        document.body.classList.add('listening');
    } else {
        document.body.classList.remove('listening');
    }
}

// Function called from UI to wake Python
function wake_jarvis() {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.wake_up();
    }
}

// Function called from UI to close Python app
function close_jarvis() {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.close_app();
    }
}
