import os
from bs4 import BeautifulSoup

FORM_SCRIPT = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    const leadForms = document.querySelectorAll('form');
    
    leadForms.forEach(form => {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (!submitBtn) return;

        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();

            const nameInput = form.querySelector('input[type="text"]');
            const phoneInput = form.querySelector('input[type="tel"]');
            const selectInputs = form.querySelectorAll('select');
            let issueSelect = selectInputs.length > 0 ? selectInputs[0] : null;

            if (nameInput && !nameInput.value.trim()) {
                alert('Please enter your name.');
                nameInput.focus();
                return;
            }
            if (phoneInput && !phoneInput.value.trim()) {
                alert('Please enter your phone number.');
                phoneInput.focus();
                return;
            }

            submitBtn.innerHTML = 'Sending...';
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.7';

            const formData = new URLSearchParams();
            formData.append('name', nameInput && nameInput.value ? nameInput.value : 'Not provided');
            formData.append('email', phoneInput && phoneInput.value ? phoneInput.value : 'Not provided');
            formData.append('concern', issueSelect && issueSelect.value ? issueSelect.value : 'Not provided');
            formData.append('pageUrl', window.location.href);

            const GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbwWpGXg3JMJnxyzUlJHPlQRnE_R2Dh6oFvapMureXQWG_0bLOBtN_e7f5s5jnKRdcG-/exec';

            fetch(GOOGLE_SCRIPT_URL, {
                method: 'POST',
                body: formData,
                mode: 'no-cors'
            })
            .then(() => {
                form.innerHTML = `
                    <div style="text-align: center; padding: 20px 10px;">
                        <div style="color: #b8963a; font-size: 40px; margin-bottom: 10px;">✓</div>
                        <h4 style="font-family: 'Cormorant Garamond', serif; font-size: 26px; color: #1a1410; margin-bottom: 10px; font-weight: 600;">Request Received</h4>
                        <p style="font-size: 14px; color: #6b5f53; line-height: 1.5; font-family: 'DM Sans', sans-serif;">
                            Your information has been securely routed. We will be in touch shortly.
                        </p>
                    </div>
                `;
            })
            .catch(error => {
                console.error('Error:', error);
                submitBtn.innerHTML = 'Error. Please Try Again.';
                submitBtn.disabled = false;
                submitBtn.style.opacity = '1';
            });
        });
    });
});
</script>
"""

def inject_script_to_ny_forms(base_dir):
    script_soup = BeautifulSoup(FORM_SCRIPT, 'html.parser')
    script_tag = script_soup.script
    script_id_string = "AKfycbwWpGXg3JMJnxyzUlJHPlQRnE_R2Dh6oFvapMureXQWG_0bLOBtN_e7f5s5jnKRdcG-"

    count = 0

    for root, dirs, files in os.walk(base_dir):
        for file_name in files:
            if file_name.endswith('.html'):
                file_path = os.path.join(root, file_name)
                
                with open(file_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()

                soup = BeautifulSoup(html_content, 'html.parser')
                has_form = soup.find('form')
                already_injected = script_id_string in html_content
                
                if has_form and not already_injected:
                    if soup.body:
                        soup.body.append(script_tag)
                        with open(file_path, 'w', encoding='utf-8') as file:
                            # Using str() preserves formatting better here
                            file.write(str(soup))
                        print(f"✓ SUCCESS: Injected script into {file_path}")
                        count += 1
                else:
                    # DIAGNOSTIC OUTPUT
                    # We only print the warning if it's one of your known silo pages to avoid cluttering the screen with unrelated files
                    if file_name in ['parent-advocacy-guide.html', 'special-ed-updates.html', 'partners.html', 'discipline-rights.html', 'evaluation-process.html', 'leadership-directory.html']:
                        if not has_form:
                            print(f"⚠️ SKIPPED: {file_path} -> REASON: No <form> tag exists in this file!")
                        elif already_injected:
                            print(f"⏭️ SKIPPED: {file_path} -> REASON: The script is already inside this file.")

    print(f"\nFinished! Successfully added the form script to {count} new files.")

if __name__ == "__main__":
    print("Scanning New York districts for lead capture forms...")
    inject_script_to_ny_forms('districts')