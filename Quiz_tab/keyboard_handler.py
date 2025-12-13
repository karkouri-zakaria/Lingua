from streamlit import components, session_state

def keyboard_handler():
    """Add keyboard event listeners for flashcard navigation and answer controls."""
    
    keyboard_js = """
    <script>
    const doc = window.parent.document;
    
    function handleKeyPress(e) {
        // Prevent default behavior for arrow keys
        if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
            e.preventDefault();
        }
        
        // Get button elements
        const buttons = doc.querySelectorAll('button');
        
        switch(e.key) {
            case 'ArrowLeft':
                // Click wrong button (✖)
                buttons.forEach(btn => {
                    if (btn.textContent.includes('✖')) {
                        btn.click();
                    }
                });
                break;
            case 'ArrowRight':
                // Click correct button (✔)
                buttons.forEach(btn => {
                    if (btn.textContent.includes('✔')) {
                        btn.click();
                    }
                });
                break;
            case 'ArrowUp':
                // Previous card
                const numberInput = doc.querySelector('input[type="number"]');
                if (numberInput && numberInput.value > numberInput.min) {
                    numberInput.value = parseInt(numberInput.value) - 1;
                    numberInput.dispatchEvent(new Event('input', { bubbles: true }));
                    numberInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
                break;
            case 'ArrowDown':
                // Next card
                const numberInputDown = doc.querySelector('input[type="number"]');
                if (numberInputDown && numberInputDown.value < numberInputDown.max) {
                    numberInputDown.value = parseInt(numberInputDown.value) + 1;
                    numberInputDown.dispatchEvent(new Event('input', { bubbles: true }));
                    numberInputDown.dispatchEvent(new Event('change', { bubbles: true }));
                }
                break;
            case ' ':
                // Spacebar: Toggle answer expander
                e.preventDefault();
                const expanders = doc.querySelectorAll('[data-testid="stExpander"]');
                expanders.forEach(exp => {
                    const summary = exp.querySelector('summary');
                    if (summary && summary.textContent.includes('Answer')) {
                        summary.click();
                    }
                });
                break;
        }
    }
    
    // Remove old listener if exists
    if (window.keyboardHandlerAttached) {
        doc.removeEventListener('keydown', window.keyboardHandler);
    }
    
    // Attach new listener
    window.keyboardHandler = handleKeyPress;
    doc.addEventListener('keydown', handleKeyPress);
    window.keyboardHandlerAttached = true;
    </script>
    """
    
    components.html(keyboard_js, height=0)
