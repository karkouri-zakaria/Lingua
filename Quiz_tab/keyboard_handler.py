import streamlit.components.v1 as components
def keyboard_handler():    
    keyboard_js = """
    <script>
    (function() {
        const doc = window.parent.document;
        const keyMap = {
            'ArrowDown':    { text: '✖' },    // Wrong
            'ArrowUp':      { text: '✔' },    // Correct
            'ArrowRight':   { text: '➕' },    // Next/Add
            'ArrowLeft':    { text: '➖' },    // Prev/Subtract
            'Shift':        { text: 'Hint' }, // Hint
            'e':            { text: '🪣' }, // Clear
            'q':            { text: '🗑️' }, // Quit
            'u':            { text: 'Upload' }, // Upload
            'l':            { text: 'Last file' }, // Last file
            'c':            { text: '♾️' }, // Continue
            ' ':            { action: 'toggleAnswer' }, // Spacebar
            'AltGraph':     { action: 'playAudio' },    // Play Audio
            'Alt':          { action: 'focusInput' },    // Focus 
            'i':            { action: 'clickUnanswered' }, // Unanswered
        };
        function handleKeyPress(e) {
            const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
            if (!keyMap[key]) return;
            if (!e.ctrlKey && key !== 'AltGraph' && key !== 'Alt') {
                return;
            }
            e.preventDefault();
            const target = keyMap[key];
            if (target.text) {
                // Find button by text content (using Array.from to use .find for efficiency)
                const buttons = Array.from(doc.getElementsByTagName('button'));
                const btn = buttons.find(b => b.textContent.includes(target.text));
                if (btn) btn.click();
            } 
            else if (target.action === 'toggleAnswer') {
                // Toggle Streamlit expander
                const expanders = Array.from(doc.querySelectorAll('[data-testid="stExpander"]'));
                const answerExpander = expanders.find(exp => {
                    const summary = exp.querySelector('summary');
                    return summary && summary.textContent.includes('Answer');
                });
                if (answerExpander) {
                    answerExpander.querySelector('summary').click();
                }
            }
            else if (target.action === 'playAudio') {
                const audio = doc.querySelector('audio');
                if (audio) audio.play();
            }
            else if (target.action === 'focusInput') {
                const textInput = doc.querySelector('input[aria-label="Type your answer here :"]');
                if (textInput) textInput.focus();
            }
            else if (target.action === 'clickUnanswered') {
                const buttons = Array.from(doc.getElementsByTagName('button'));
                const rangeBtn = buttons.find(b => /^\d+(-\d+)?$/.test(b.textContent.trim()));
                if (rangeBtn) {
                    rangeBtn.click();
                } else {
                    const popoverBtn = buttons.find(b => b.textContent.includes('📋'));
                    if (popoverBtn) popoverBtn.click();
                }
            }
        }
        // Clean up previous event listener to prevent duplicates
        if (window.keyboardHandler) {
            doc.removeEventListener('keydown', window.keyboardHandler);
        }
        // Attach new listener
        window.keyboardHandler = handleKeyPress;
        doc.addEventListener('keydown', handleKeyPress);
    })();
    </script>
    """
    components.html(keyboard_js, height=0)