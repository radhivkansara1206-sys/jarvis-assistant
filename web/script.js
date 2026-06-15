// Eel functions to be called from Python
eel.expose(update_status);
function update_status(mainText, subText, isListening) {
    document.getElementById('status-text').innerText = mainText;
    document.getElementById('sub-text').innerText = subText;

    if (isListening) {
        document.body.classList.add('listening');
    } else {
        document.body.classList.remove('listening');
    }
}

// Example usage to test without python (remove or ignore)
// setTimeout(() => update_status("LISTENING", "Processing audio...", true), 2000);
// setTimeout(() => update_status("ANALYZING", "Accessing neural net...", false), 5000);
