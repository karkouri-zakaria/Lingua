import streamlit.components.v1 as components

def keyboard_handler():
    """Add keyboard event listeners for flashcard navigation and answer controls."""
    
    keyboard_js = """
    <script>
    const doc = window.parent.document;
    
    function handleKeyPress(e) {
        // Prevent default behavior for arrow keys
        if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',' '].includes(e.key)) {
            if (!e.ctrlKey) return;
            e.preventDefault();
        }
        
        // Get button elements
        const buttons = doc.querySelectorAll('button');
        
        switch(e.key) {
            case 'ArrowDown':
                // Click wrong button (✖)
                buttons.forEach(btn => {
                    if (btn.textContent.includes('✖')) {
                        btn.click();
                    }
                });
                break;
            case 'ArrowUp':
                // Click correct button (✔)
                buttons.forEach(btn => {
                    if (btn.textContent.includes('✔')) {
                        btn.click();
                    }
                });
                break;
            case 'ArrowRight':
                // Click previous card
                buttons.forEach(btn => {
                    if (btn.textContent.includes('➕')) {
                        btn.click();
                    }
                });
                break;
            case 'ArrowLeft':
                // Click next card
                buttons.forEach(btn => {
                    if (btn.textContent.includes('➖')) {
                        btn.click();
                    }
                });
            case ' ':
                // Spacebar: Toggle answer expander
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
