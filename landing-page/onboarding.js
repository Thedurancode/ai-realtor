// ===== Onboarding Wizard Configuration =====

const ONBOARDING_STEPS = [
    {
        id: 'business_card',
        emoji: '💳',
        title: 'Upload Your Business Card',
        subtitle: 'Snap a photo of your business card and we\'ll automatically fill in your details',
        type: 'business_card_upload',
        fields: [
            {
                name: 'business_card_image',
                label: 'Business Card Image',
                type: 'file',
                accept: 'image/*',
                required: false,
                hint: 'Take a clear photo of your business card or upload an existing image'
            }
        ],
        manual_fields: [
            {
                name: 'first_name',
                label: 'First Name',
                type: 'text',
                placeholder: 'John',
                required: true
            },
            {
                name: 'last_name',
                label: 'Last Name',
                type: 'text',
                placeholder: 'Smith',
                required: true
            },
            {
                name: 'age',
                label: 'Age',
                type: 'number',
                placeholder: '30',
                required: true,
                min: 18,
                max: 100
            },
            {
                name: 'city',
                label: 'City',
                type: 'text',
                placeholder: 'Miami',
                required: true
            },
            {
                name: 'address',
                label: 'Address',
                type: 'text',
                placeholder: '123 Main Street',
                required: false
            },
            {
                name: 'phone',
                label: 'Phone Number',
                type: 'tel',
                placeholder: '+1 (555) 123-4567',
                required: true
            },
            {
                name: 'email',
                label: 'Email Address',
                type: 'email',
                placeholder: 'john@example.com',
                required: true
            },
            {
                name: 'business_name',
                label: 'Business Name',
                type: 'text',
                placeholder: 'Smith Realty Group',
                required: true
            },
            {
                name: 'license_number',
                label: 'Real Estate License Number',
                type: 'text',
                placeholder: 'RK12345678',
                required: false,
                skipable: true,
                hint: 'Optional - you can add this later'
            }
        ]
    },
    {
        id: 'schedule',
        emoji: '📅',
        title: 'Your Weekly Schedule',
        subtitle: 'When do you typically work? We\'ll respect your time',
        type: 'schedule',
        days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    },
    {
        id: 'branding',
        emoji: '🎨',
        title: 'Your Brand Colors',
        subtitle: 'Customize the look and feel of your AI assistant',
        fields: [
            {
                name: 'logo',
                label: 'Business Logo (Optional)',
                type: 'file',
                accept: 'image/*',
                required: false,
                hint: 'Upload your logo to personalize your AI assistant'
            }
        ],
        colors: [
            { name: 'primary_color', label: 'Primary Color', default: '#f97316' },
            { name: 'secondary_color', label: 'Secondary Color', default: '#3b82f6' },
            { name: 'accent_color', label: 'Accent Color', default: '#22c55e' },
            { name: 'background_color', label: 'Background Color', default: '#0a0a0b' },
            { name: 'text_color', label: 'Text Color', default: '#ffffff' }
        ]
    },
    {
        id: 'contacts',
        emoji: '👥',
        title: 'Import Your Contacts',
        subtitle: 'Upload your contacts so your AI assistant knows who you work with',
        type: 'contacts_upload',
        fields: [
            {
                name: 'contacts_file',
                label: 'Upload Contacts File',
                type: 'file',
                accept: '.csv,.xlsx,.vcf',
                required: false,
                hint: 'Supports CSV, Excel, or vCard files'
            }
        ]
    },
    {
        id: 'social',
        emoji: '📱',
        title: 'Your Social Media',
        subtitle: 'Connect your social channels for a complete picture',
        type: 'social_media',
        platforms: [
            { name: 'facebook', icon: '📘', placeholder: 'facebook.com/yourbusiness' },
            { name: 'instagram', icon: '📷', placeholder: '@yourbusiness' },
            { name: 'linkedin', icon: '💼', placeholder: 'linkedin.com/in/yourprofile' },
            { name: 'twitter', icon: '🐦', placeholder: '@yourhandle' },
            { name: 'tiktok', icon: '🎵', placeholder: '@yourbusiness' },
            { name: 'youtube', icon: '📺', placeholder: 'youtube.com/@yourchannel' }
        ]
    },
    {
        id: 'music',
        emoji: '🎵',
        title: 'Work Vibes',
        subtitle: 'What music keeps you motivated while you work?',
        type: 'music_preferences',
        genres: [
            'Lo-Fi', 'Jazz', 'Classical', 'Pop', 'Rock', 'Hip-Hop',
            'Electronic', 'Country', 'R&B', 'Indie', 'Ambient',
            'Reggae', 'Latin', 'K-Pop', 'Podcasts', 'Silence'
        ]
    },
    {
        id: 'weekend',
        emoji: '🌴',
        title: 'Weekend Schedule',
        subtitle: 'Do you work weekends? We won\'t judge either way',
        type: 'schedule',
        days: ['Saturday', 'Sunday']
    },
    {
        id: 'contracts',
        emoji: '📄',
        title: 'Your Contracts',
        subtitle: 'What contracts do you typically use in your deals?',
        type: 'contracts',
        options: [
            { value: 'purchase_agreement', label: 'Purchase Agreement', icon: '📝', desc: 'Standard offer to purchase' },
            { value: 'listing_agreement', label: 'Listing Agreement', icon: '🏠', desc: 'Seller representation' },
            { value: 'lease_agreement', label: 'Lease Agreement', icon: '🔑', desc: 'Rental contracts' },
            { value: 'disclosure', label: 'Disclosure Forms', icon: '⚠️', desc: 'Property disclosures' },
            { value: 'closing_statement', label: 'Closing Statement', icon: '💰', desc: 'HUD-1 / CD' },
            { value: 'inspection_contingency', label: 'Inspection Contingency', icon: '🔍', desc: 'Inspection clauses' },
            { value: 'financing_addendum', label: 'Financing Addendum', icon: '🏦', desc: 'Loan contingencies' },
            { value: 'lead_paint', label: 'Lead Paint Disclosure', icon: '🎨', desc: 'Federal requirement' }
        ]
    },
    {
        id: 'calendar',
        emoji: '🗓️',
        title: 'Calendar Preferences',
        subtitle: 'Would you like AI to help manage your calendar? (No setup required now)',
        type: 'calendar_connect',
        fields: [
            {
                name: 'connect_calendar',
                label: 'Enable Calendar Integration',
                type: 'checkbox',
                description: 'Your AI can later help schedule showings, closings, and follow-ups. You\'ll connect your calendar when you\'re ready.',
                required: false
            }
        ]
    },
    {
        id: 'locations',
        emoji: '📍',
        title: 'Business Locations',
        subtitle: 'Where do you do business? Help us know your market',
        type: 'locations',
        fields: [
            {
                name: 'primary_market',
                label: 'Primary Market',
                type: 'text',
                placeholder: 'Miami-Dade County, FL',
                required: true
            },
            {
                name: 'secondary_markets',
                label: 'Secondary Markets',
                type: 'textarea',
                placeholder: 'Broward County, FL\nPalm Beach County, FL',
                required: false,
                hint: 'One per line'
            },
            {
                name: 'service_radius',
                label: 'Service Radius',
                type: 'select',
                options: ['5 miles', '10 miles', '25 miles', '50 miles', 'Statewide', 'Nationwide'],
                required: true
            },
            {
                name: 'office_locations',
                label: 'Office Locations',
                type: 'textarea',
                placeholder: 'Downtown Miami Office\n123 Brickell Ave, Miami, FL 33131',
                required: false,
                hint: 'One per line'
            }
        ]
    },
    {
        id: 'assistant_identity',
        emoji: '🤖',
        title: 'Your AI Assistant',
        subtitle: 'Finally, let\'s customize your AI assistant\'s personality',
        type: 'assistant_identity',
        fields: [
            {
                name: 'assistant_name',
                label: 'Assistant Name',
                type: 'text',
                placeholder: 'Clawbot',
                required: true
            },
            {
                name: 'assistant_style',
                label: 'Communication Style',
                type: 'select',
                options: [
                    'Professional & Formal',
                    'Friendly & Casual',
                    'Concise & Direct',
                    'Enthusiastic & Energetic',
                    'Witty & Humorous'
                ],
                required: true
            }
        ],
        personality: [
            { name: 'responsiveness', label: 'Responsiveness', left: 'Relaxed', right: 'Immediate' },
            { name: 'proactivity', label: 'Proactivity', left: 'Reactive', right: 'Proactive' },
            { name: 'detail_level', label: 'Detail Level', left: 'Brief', right: 'Detailed' },
            { name: 'formality', label: 'Formality', left: 'Casual', right: 'Formal' }
        ]
    }
];

// ===== State Management =====

let currentStep = 0;
let formData = {
    first_name: '',
    last_name: '',
    age: '',
    city: '',
    address: '',
    phone: '',
    email: '',
    schedule: {},
    business_name: '',
    logo: null,
    colors: {},
    contacts_file: null,
    social_media: {},
    music_preferences: [],
    weekend_schedule: {},
    contracts: [],
    connect_calendar: false,
    primary_market: '',
    secondary_markets: '',
    service_radius: '',
    office_locations: '',
    assistant_name: '',
    assistant_style: '',
    personality: {}
};

// ===== DOM Elements =====

const form = document.getElementById('onboardingForm');
const progressFill = document.getElementById('progressFill');
const stepIndicators = document.getElementById('stepIndicators');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const submitBtn = document.getElementById('submitBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const successModal = document.getElementById('successModal');

// ===== Google Places Autocomplete =====

let addressAutocomplete = null;

function initGooglePlaces() {
    if (typeof google === 'undefined' || !google.maps || !google.maps.places) {
        console.warn('Google Places API not loaded');
        return;
    }

    // Wait for the address field to be rendered
    const initAutocomplete = () => {
        const addressInput = document.querySelector('input[name="address"]');
        if (addressInput && !addressAutocomplete) {
            // Create autocomplete instance
            addressAutocomplete = new google.maps.places.Autocomplete(addressInput, {
                types: ['address'],
                componentRestrictions: { country: 'us' }, // Restrict to US addresses
                fields: ['address_components', 'formatted_address', 'geometry', 'name']
            });

            // Listen for place selection
            addressAutocomplete.addListener('place_changed', handleAddressSelect);

            // Add visual indicator that autocomplete is active
            addressInput.setAttribute('autocomplete', 'off');
            addressInput.setAttribute('data-autocomplete-enabled', 'true');
        }
    };

    // Try to initialize immediately
    initAutocomplete();

    // Also try when step 1 is shown (in case DOM isn't ready yet)
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length > 0) {
                const addressInput = document.querySelector('input[name="address"]');
                if (addressInput && !addressAutocomplete) {
                    initAutocomplete();
                }
            }
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // Clean up observer after 5 seconds
    setTimeout(() => observer.disconnect(), 5000);
}

function handleAddressSelect() {
    if (!addressAutocomplete) return;

    const place = addressAutocomplete.getPlace();

    if (!place || !place.address_components) {
        // User entered a place that wasn't in the autocomplete results
        return;
    }

    // Parse address components
    const components = place.address_components;
    const addressData = {
        street_number: null,
        street_name: null,
        city: null,
        state: null,
        zip_code: null,
        formatted_address: place.formatted_address
    };

    // Extract address components
    components.forEach(component => {
        const types = component.types;
        const longName = component.long_name;
        const shortName = component.short_name;

        if (types.includes('street_number')) {
            addressData.street_number = longName;
        } else if (types.includes('route')) {
            addressData.street_name = longName;
        } else if (types.includes('locality')) {
            addressData.city = longName;
        } else if (types.includes('administrative_area_level_1')) {
            addressData.state = shortName; // Use state abbreviation
        } else if (types.includes('postal_code')) {
            addressData.zip_code = longName;
        }
    });

    // Fill in the address field with formatted address
    const addressInput = document.querySelector('input[name="address"]');
    if (addressInput) {
        addressInput.value = addressData.formatted_address;
        // Trigger change event
        addressInput.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // Auto-fill city if it's empty
    if (addressData.city) {
        const cityInput = document.querySelector('input[name="city"]');
        if (cityInput && !cityInput.value) {
            cityInput.value = addressData.city;
            cityInput.style.borderColor = 'var(--success)';
            cityInput.style.boxShadow = '0 0 10px rgba(34, 197, 94, 0.2)';

            setTimeout(() => {
                cityInput.style.borderColor = '';
                cityInput.style.boxShadow = '';
            }, 1500);

            showNotification('Address auto-filled! City added from Google Maps ✨');
        }
    }

    // Log for debugging
    console.log('Google Places address data:', addressData);
}

// ===== Initialization =====

function init() {
    renderStepIndicators();
    renderSteps();
    updateProgress();
    showStep(0);
    setupEventListeners();

    // Initialize Google Places autocomplete
    if (typeof initGooglePlaces === 'function') {
        initGooglePlaces();
    }

    // Check if returning from Stripe payment
    checkPaymentReturn();
}

// ===== Render Functions =====

function renderStepIndicators() {
    stepIndicators.innerHTML = ONBOARDING_STEPS.map((_, index) => `
        <div class="step-indicator" data-step="${index}"></div>
    `).join('');
}

function renderSteps() {
    let stepHTML = '';
    let stepNumber = 1;

    ONBOARDING_STEPS.forEach((step, stepIndex) => {
        stepHTML += `
            <div class="form-step" data-step="${stepIndex}">
                <div class="step-header">
                    <span class="step-emoji">${step.emoji}</span>
                    <span class="step-number">Step ${stepNumber} of ${ONBOARDING_STEPS.length}</span>
                    <h2 class="step-title">${step.title}</h2>
                    <p class="step-subtitle">${step.subtitle}</p>
                </div>
                <div class="step-content">
                    ${renderStepContent(step, stepIndex)}
                </div>
            </div>
        `;
        stepNumber++;
    });

    form.innerHTML = stepHTML;
}

function renderStepContent(step, stepIndex) {
    switch (step.type) {
        case 'business_card_upload':
            return renderBusinessCardStep(step);
        case 'schedule':
            return renderScheduleStep(step);
        case 'contacts_upload':
            return renderContactsStep(step);
        case 'social_media':
            return renderSocialMediaStep(step);
        case 'music_preferences':
            return renderMusicStep(step);
        case 'contracts':
            return renderContractsStep(step);
        case 'calendar_connect':
            return renderCalendarStep(step);
        case 'locations':
            return renderLocationsStep(step);
        case 'assistant_identity':
            return renderAssistantIdentityStep(step);
        default:
            return renderDefaultStep(step);
    }
}

function renderDefaultStep(step) {
    let html = '';

    // Render regular fields
    if (step.fields) {
        step.fields.forEach(field => {
            html += renderField(field);
        });
    }

    // Render color pickers if present
    if (step.colors) {
        html += '<div class="form-group"><label>Brand Colors</label>';
        html += '<div class="color-picker-group">';
        step.colors.forEach(color => {
            html += `
                <div class="color-picker-item">
                    <div class="color-input-wrapper">
                        <input type="color" name="${color.name}" value="${color.default}">
                        <input type="text" name="${color.name}_text" value="${color.default}">
                    </div>
                </div>
            `;
        });
        html += '</div>';
        html += '<div class="color-presets">';
        const presets = [
            ['#f97316', '#3b82f6', '#22c55e', '#0a0a0b', '#ffffff'],
            ['#ec4899', '#8b5cf6', '#06b6d4', '#0a0a0b', '#ffffff'],
            ['#ef4444', '#f59e0b', '#10b981', '#0a0a0b', '#ffffff'],
            ['#6366f1', '#8b5cf6', '#d946ef', '#0a0a0b', '#ffffff']
        ];
        presets.forEach(preset => {
            html += `<button type="button" class="color-preset-btn" style="background: linear-gradient(135deg, ${preset[0]} 0%, ${preset[1]} 50%, ${preset[2]} 100%)" data-preset='${JSON.stringify(preset)}'></button>`;
        });
        html += '</div></div>';
    }

    return html;
}

function renderBusinessCardStep(step) {
    let html = `
        <div class="business-card-upload-container">
            <!-- Large Business Card Upload Area -->
            <div class="business-card-upload" id="businessCardUpload" onclick="document.getElementById('business_card_image').click()">
                <div class="business-card-upload-content">
                    <svg class="business-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="2" y="5" width="20" height="14" rx="2" />
                        <line x1="2" y1="10" x2="22" y2="10" />
                    </svg>
                    <h3>Upload Your Business Card</h3>
                    <p class="business-card-upload-text">Take a photo or upload an image of your business card</p>
                    <p class="business-card-hint">We'll automatically extract your information ✨</p>
                    <div class="business-card-preview" id="businessCardPreview" style="display: none;">
                        <img id="businessCardImage" src="" alt="Business card preview">
                    </div>
                </div>
                <input type="file" name="business_card_image" accept="image/*" style="display: none;" onchange="handleBusinessCardUpload(this)">
                <div class="business-card-actions" id="businessCardActions" style="display: none;">
                    <button type="button" class="btn btn-secondary btn-small" onclick="event.stopPropagation(); removeBusinessCard()">
                        Remove
                    </button>
                    <button type="button" class="btn btn-primary btn-small" onclick="event.stopPropagation(); document.getElementById('business_card_image').click()">
                        Change Photo
                    </button>
                </div>
            </div>

            <!-- Divider -->
            <div class="manual-entry-divider">
                <div class="divider-line"></div>
                <span class="divider-text">Or enter your details manually</span>
                <div class="divider-line"></div>
            </div>

            <!-- Manual Entry Form -->
            <div class="manual-entry-form" id="manualEntryForm">
    `;

    // Render manual fields
    if (step.manual_fields) {
        step.manual_fields.forEach(field => {
            html += renderField(field);
        });
    }

    html += `
            </div>
        </div>
    `;

    return html;
}

function renderScheduleStep(step) {
    const scheduleKey = step.id === 'weekend' ? 'weekend_schedule' : 'schedule';

    let html = '<div class="schedule-grid">';
    step.days.forEach(day => {
        html += `
            <div class="day-schedule">
                <div class="day-schedule-header">
                    <label class="day-schedule-label">${day}</label>
                    <label class="checkbox-item" style="padding: 0.25rem 0.5rem;">
                        <input type="checkbox" name="${scheduleKey}_${day.toLowerCase()}_off" checked>
                        <span style="font-size: 0.8rem;">Off</span>
                    </label>
                </div>
                <div class="day-schedule-times">
                    <input type="time" class="time-input" name="${scheduleKey}_${day.toLowerCase()}_start" value="09:00">
                    <span>to</span>
                    <input type="time" class="time-input" name="${scheduleKey}_${day.toLowerCase()}_end" value="17:00">
                </div>
            </div>
        `;
    });
    html += '</div>';
    return html;
}

function renderContactsStep(step) {
    return `
        <div class="file-upload" id="contactsUpload" onclick="document.getElementById('contacts_file').click()">
            <svg class="file-upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <p class="file-upload-text">Drop your contacts file here or click to browse</p>
            <p class="form-hint">${step.fields[0].hint}</p>
            <input type="file" name="contacts_file" accept="${step.fields[0].accept}" style="display: none;" onchange="handleFileUpload(this, 'contactsUpload')">
            <span class="file-upload-filename" id="contactsFilename"></span>
        </div>
    `;
}

function renderSocialMediaStep(step) {
    let html = '<div class="social-media-grid">';
    step.platforms.forEach(platform => {
        html += `
            <div class="social-input-group">
                <span class="social-icon">${platform.icon}</span>
                <input type="text" class="social-input" name="social_${platform.name}" placeholder="${platform.placeholder}">
            </div>
        `;
    });
    html += '</div>';
    return html;
}

function renderMusicStep(step) {
    let html = '<div class="music-grid">';
    step.genres.forEach(genre => {
        html += `
            <label class="music-tag">
                <input type="checkbox" name="music_genre" value="${genre}">
                <span>${genre}</span>
            </label>
        `;
    });
    html += '</div>';
    return html;
}

function renderContractsStep(step) {
    let html = '<div class="contracts-grid">';

    // Group into categories for better layout
    const categories = {
        'Essential Contracts': step.options.slice(0, 2),  // Purchase, Listing
        'Disclosures & Addendums': step.options.slice(2, 5),  // Lease, Disclosure, Closing
        'Contingencies': step.options.slice(5, 7),  // Inspection, Financing
        'Required Forms': step.options.slice(7)  // Lead paint
    };

    Object.entries(categories).forEach(([category, options]) => {
        html += `
            <div class="contract-category">
                <h4 class="contract-category-title">${category}</h4>
                <div class="contract-category-items">
        `;

        options.forEach(option => {
            const inputId = `contract_${option.value}`;
            html += `
                <label class="contract-item" for="${inputId}">
                    <input type="checkbox" name="contracts" value="${option.value}" id="${inputId}">
                    <span class="contract-icon">${option.icon}</span>
                    <div class="contract-info">
                        <span class="contract-name">${option.label}</span>
                        <span class="contract-desc">${option.desc}</span>
                    </div>
                    <span class="contract-checkbox"></span>
                </label>
            `;
        });

        html += `
                </div>
            </div>
        `;
    });

    html += '</div>';

    // Add helpful hint
    html += `
        <div class="contracts-hint">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            <span>Select all contracts that apply to your typical real estate transactions</span>
        </div>
    `;

    return html;
}

function renderCalendarStep(step) {
    return `
        <div class="calendar-pref-container">
            <div class="calendar-option-card">
                <div class="calendar-option-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="16" y1="2" x2="16" y2="6"></line>
                        <line x1="8" y1="2" x2="8" y2="6"></line>
                        <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                </div>
                <div class="calendar-option-content">
                    <label class="calendar-option-toggle">
                        <input type="checkbox" name="connect_calendar">
                        <span class="toggle-slider"></span>
                        <span class="toggle-label">${step.fields[0].label}</span>
                    </label>
                    <p class="calendar-option-desc">${step.fields[0].description}</p>
                    <div class="calendar-features">
                        <div class="calendar-feature">
                            <span class="calendar-feature-icon">✓</span>
                            <span>Smart scheduling suggestions</span>
                        </div>
                        <div class="calendar-feature">
                            <span class="calendar-feature-icon">✓</span>
                            <span>Automatic conflict detection</span>
                        </div>
                        <div class="calendar-feature">
                            <span class="calendar-feature-icon">✓</span>
                            <span>One-click setup when you're ready</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="calendar-note">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                <span>No API key needed now. Just enable this feature to use it later!</span>
            </div>
        </div>
    `;
}

function renderLocationsStep(step) {
    let html = '';
    step.fields.forEach(field => {
        html += renderField(field);
    });
    return html;
}

function renderAssistantIdentityStep(step) {
    let html = `
        <div class="assistant-identity-preview">
            <div class="assistant-avatar-preview">🤖</div>
            <div class="assistant-details">
                <h4 id="previewName">Your AI Assistant</h4>
                <p id="previewStyle">Ready to help you close more deals</p>
            </div>
        </div>
    `;

    step.fields.forEach(field => {
        html += renderField(field);
    });

    html += '<div class="personality-sliders">';
    step.personality.forEach(trait => {
        html += `
            <div class="slider-group">
                <div class="slider-label">
                    <span>${trait.label}</span>
                    <span>${trait.left} / ${trait.right}</span>
                </div>
                <input type="range" class="slider-input" name="personality_${trait.name}" min="0" max="100" value="50">
            </div>
        `;
    });
    html += '</div>';

    return html;
}

function renderField(field) {
    let html = `<div class="form-group">`;

    if (field.type === 'textarea') {
        html += `
            <label>${field.label}${field.required ? '<span class="required">*</span>' : ''}</label>
            <textarea name="${field.name}" placeholder="${field.placeholder || ''}" ${field.required ? 'required' : ''} rows="4"></textarea>
        `;
    } else if (field.type === 'select') {
        html += `
            <label>${field.label}${field.required ? '<span class="required">*</span>' : ''}</label>
            <select name="${field.name}" ${field.required ? 'required' : ''}>
                <option value="">Select an option</option>
                ${field.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
            </select>
        `;
    } else if (field.type === 'file') {
        html += `
            <label>${field.label}${field.required ? '<span class="required">*</span>' : ''}</label>
            <div class="file-upload" id="${field.name}_upload" onclick="document.getElementById('${field.name}').click()">
                <svg class="file-upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="17 8 12 3 7 8"></polyline>
                    <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                <p class="file-upload-text">Click to upload or drag and drop</p>
                <input type="file" name="${field.name}" accept="${field.accept || '*'}" style="display: none;" onchange="handleFileUpload(this, '${field.name}_upload')">
                <span class="file-upload-filename" id="${field.name}_filename"></span>
            </div>
        `;
    } else {
        const attrs = field.type === 'number' ? `min="${field.min || ''}" max="${field.max || ''}"` : '';
        const skipableAttr = field.skipable ? 'data-skipable="true"' : '';
        html += `
            <label>${field.label}${field.required ? '<span class="required">*</span>' : ''}</label>
            <div class="input-with-skip">
                <input type="${field.type}" name="${field.name}" placeholder="${field.placeholder || ''}" ${field.required ? 'required' : ''} ${attrs} ${skipableAttr}>
                ${field.skipable ? `<button type="button" class="skip-btn" onclick="skipField('${field.name}')">Skip for now</button>` : ''}
            </div>
        `;
    }

    if (field.hint) {
        html += `<p class="form-hint">${field.hint}</p>`;
    }

    html += '</div>';

    return html;
}

// ===== Event Handlers =====

function setupEventListeners() {
    prevBtn.addEventListener('click', () => navigateStep(-1));
    nextBtn.addEventListener('click', () => navigateStep(1));
    form.addEventListener('submit', handleSubmit);

    // Color picker sync
    document.addEventListener('input', (e) => {
        if (e.target.type === 'color') {
            const textInput = document.querySelector(`input[name="${e.target.name}_text"]`);
            if (textInput) textInput.value = e.target.value;
        }
        if (e.target.type === 'text' && e.target.name.endsWith('_text')) {
            const colorInput = document.querySelector(`input[name="${e.target.name.replace('_text', '')}"]`);
            if (colorInput && /^#[0-9A-Fa-f]{6}$/.test(e.target.value)) {
                colorInput.value = e.target.value;
            }
        }
    });

    // Color preset buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('color-preset-btn')) {
            const preset = JSON.parse(e.target.dataset.preset);
            const colorNames = ['primary_color', 'secondary_color', 'accent_color', 'background_color', 'text_color'];
            preset.forEach((color, i) => {
                const colorInput = document.querySelector(`input[name="${colorNames[i]}"]`);
                const textInput = document.querySelector(`input[name="${colorNames[i]}_text"]`);
                if (colorInput) colorInput.value = color;
                if (textInput) textInput.value = color;
            });
        }
    });

    // Music tag selection
    document.addEventListener('change', (e) => {
        if (e.target.name === 'music_genre') {
            e.target.closest('.music-tag').classList.toggle('selected', e.target.checked);
        }
    });

    // Assistant name preview
    document.addEventListener('input', (e) => {
        if (e.target.name === 'assistant_name') {
            const preview = document.getElementById('previewName');
            if (preview) preview.textContent = e.target.value || 'Your AI Assistant';
        }
        if (e.target.name === 'assistant_style') {
            const preview = document.getElementById('previewStyle');
            const styles = {
                'Professional & Formal': 'Professional business assistant',
                'Friendly & Casual': 'Your friendly business partner',
                'Concise & Direct': 'Brief and to the point',
                'Enthusiastic & Energetic': 'Energized to help you succeed',
                'Witty & Humorous': 'Serious about results, not about taking myself seriously'
            };
            if (preview) preview.textContent = styles[e.target.value] || 'Ready to help you close more deals';
        }
    });

    // Day off toggle
    document.addEventListener('change', (e) => {
        if (e.target.name && e.target.name.endsWith('_off')) {
            const container = e.target.closest('.day-schedule');
            const inputs = container.querySelectorAll('.time-input');
            inputs.forEach(input => input.disabled = e.target.checked);
        }
    });
}

function handleFileUpload(input, uploadId) {
    const uploadEl = document.getElementById(uploadId);
    const filenameEl = document.getElementById(uploadId.replace('_upload', '_filename'));

    if (input.files && input.files[0]) {
        uploadEl.classList.add('has-file');
        if (filenameEl) {
            filenameEl.textContent = input.files[0].name;
        }
    }
}

function handleBusinessCardUpload(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const uploadEl = document.getElementById('businessCardUpload');
        const previewEl = document.getElementById('businessCardPreview');
        const imageEl = document.getElementById('businessCardImage');
        const actionsEl = document.getElementById('businessCardActions');
        const contentEl = uploadEl.querySelector('.business-card-upload-content');

        // Show image preview
        const reader = new FileReader();
        reader.onload = function(e) {
            imageEl.src = e.target.result;
            previewEl.style.display = 'block';
            actionsEl.style.display = 'flex';
            contentEl.classList.add('has-image');

            // Simulate OCR extraction (in real implementation, send to backend)
            setTimeout(() => {
                simulateOCRExtraction();
            }, 1000);
        };
        reader.readAsDataURL(file);

        uploadEl.classList.add('has-file');
    }
}

function removeBusinessCard() {
    const uploadEl = document.getElementById('businessCardUpload');
    const previewEl = document.getElementById('businessCardPreview');
    const imageEl = document.getElementById('businessCardImage');
    const actionsEl = document.getElementById('businessCardActions');
    const contentEl = uploadEl.querySelector('.business-card-upload-content');
    const inputEl = document.getElementById('business_card_image');

    // Reset upload
    inputEl.value = '';
    imageEl.src = '';
    previewEl.style.display = 'none';
    actionsEl.style.display = 'none';
    contentEl.classList.remove('has-image');
    uploadEl.classList.remove('has-file');

    // Clear extracted data
    clearExtractedData();
}

function simulateOCRExtraction() {
    // Simulated OCR data - in real implementation, this would come from backend
    const simulatedData = {
        first_name: 'John',
        last_name: 'Smith',
        email: 'john@smithrealty.com',
        phone: '+1 (305) 555-0123',
        business_name: 'Smith Realty Group',
        city: 'Miami'
    };

    // Fill form fields with animation
    Object.keys(simulatedData).forEach((key, index) => {
        setTimeout(() => {
            const input = document.querySelector(`[name="${key}"]`);
            if (input && !input.value) {
                input.value = simulatedData[key];
                input.style.borderColor = 'var(--success)';
                input.style.boxShadow = '0 0 10px rgba(34, 197, 94, 0.2)';

                // Flash effect
                setTimeout(() => {
                    input.style.borderColor = '';
                    input.style.boxShadow = '';
                }, 1500);
            }
        }, index * 300);
    });

    // Show success message
    showNotification('Information extracted from business card! ✨');
}

function clearExtractedData() {
    const fields = ['first_name', 'last_name', 'email', 'phone', 'business_name', 'city'];
    fields.forEach(key => {
        const input = document.querySelector(`[name="${key}"]`);
        if (input) {
            input.value = '';
        }
    });
}

function skipField(fieldName) {
    const input = document.querySelector(`input[name="${fieldName}"]`);
    const skipBtn = document.querySelector(`.skip-btn`);

    if (input) {
        input.value = '_SKIPPED_';
        input.disabled = true;
        input.style.opacity = '0.5';
        input.style.textDecoration = 'line-through';

        if (skipBtn) {
            skipBtn.textContent = 'Skipped ✓';
            skipBtn.disabled = true;
            skipBtn.style.opacity = '0.6';
        }

        showNotification('Field skipped - you can add this later in your profile settings');
    }
}

function showNotification(message) {
    // Remove existing notification
    const existing = document.querySelector('.ocr-notification');
    if (existing) existing.remove();

    // Create notification
    const notification = document.createElement('div');
    notification.className = 'ocr-notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--success);
        color: #000;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ===== Navigation =====

function navigateStep(direction) {
    const newStep = currentStep + direction;

    if (newStep < 0 || newStep >= ONBOARDING_STEPS.length) return;

    // Validate current step before moving forward
    if (direction > 0 && !validateStep(currentStep)) {
        return;
    }

    // Save current step data
    saveStepData(currentStep);

    currentStep = newStep;
    showStep(currentStep);
    updateProgress();
}

function showStep(index) {
    // Update form steps
    document.querySelectorAll('.form-step').forEach((step, i) => {
        step.classList.toggle('active', i === index);
    });

    // Update step indicators
    document.querySelectorAll('.step-indicator').forEach((indicator, i) => {
        indicator.classList.toggle('active', i === index);
        indicator.classList.toggle('completed', i < index);
    });

    // Update buttons
    prevBtn.disabled = index === 0;

    // Reinitialize Google Places autocomplete when showing step 0 (business card)
    if (index === 0 && typeof initGooglePlaces === 'function') {
        // Small delay to ensure DOM is ready
        setTimeout(() => {
            const addressInput = document.querySelector('input[name="address"]');
            if (addressInput && !addressInput.getAttribute('data-autocomplete-enabled')) {
                initGooglePlaces();
            }
        }, 100);
    }

    if (index === ONBOARDING_STEPS.length - 1) {
        nextBtn.style.display = 'none';
        submitBtn.style.display = 'inline-flex';
    } else {
        nextBtn.style.display = 'inline-flex';
        submitBtn.style.display = 'none';
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateProgress() {
    const progress = ((currentStep + 1) / ONBOARDING_STEPS.length) * 100;
    progressFill.style.width = `${progress}%`;
}

// ===== Validation & Data =====

function validateStep(index) {
    const step = ONBOARDING_STEPS[index];
    const currentStepEl = document.querySelector(`.form-step[data-step="${index}"]`);
    const requiredInputs = currentStepEl.querySelectorAll('input[required], select[required], textarea[required]');

    for (const input of requiredInputs) {
        if (!input.value.trim()) {
            input.focus();
            input.style.borderColor = 'var(--error)';
            setTimeout(() => {
                input.style.borderColor = '';
            }, 2000);
            return false;
        }
    }

    return true;
}

function saveStepData(index) {
    const step = ONBOARDING_STEPS[index];
    const currentStepEl = document.querySelector(`.form-step[data-step="${index}"]`);

    switch (step.type) {
        case 'business_card_upload':
            // Save business card file reference if uploaded
            const cardInput = currentStepEl.querySelector('input[name="business_card_image"]');
            if (cardInput && cardInput.files[0]) {
                formData.business_card_image = cardInput.files[0].name;
            }
            // Save manual fields (which include all the personal/business info)
            if (step.manual_fields) {
                step.manual_fields.forEach(field => {
                    const input = currentStepEl.querySelector(`[name="${field.name}"]`);
                    if (input) {
                        formData[field.name] = input.value;
                    }
                });
            }
            break;

        case 'schedule':
            const scheduleKey = step.id === 'weekend' ? 'weekend_schedule' : 'schedule';
            step.days.forEach(day => {
                const dayLower = day.toLowerCase();
                const isOff = currentStepEl.querySelector(`input[name="${scheduleKey}_${dayLower}_off"]`)?.checked;
                if (!isOff) {
                    formData[scheduleKey][dayLower] = {
                        start: currentStepEl.querySelector(`input[name="${scheduleKey}_${dayLower}_start"]`)?.value,
                        end: currentStepEl.querySelector(`input[name="${scheduleKey}_${dayLower}_end"]`)?.value
                    };
                } else {
                    formData[scheduleKey][dayLower] = { off: true };
                }
            });
            break;

        case 'social_media':
            step.platforms.forEach(platform => {
                const input = currentStepEl.querySelector(`input[name="social_${platform.name}"]`);
                if (input?.value) {
                    formData.social_media[platform.name] = input.value;
                }
            });
            break;

        case 'music_preferences':
            formData.music_preferences = Array.from(currentStepEl.querySelectorAll('input[name="music_genre"]:checked')).map(i => i.value);
            break;

        case 'contracts':
            formData.contracts = Array.from(currentStepEl.querySelectorAll('input[name="contracts"]:checked')).map(i => i.value);
            break;

        case 'assistant_identity':
            step.personality.forEach(trait => {
                const slider = currentStepEl.querySelector(`input[name="personality_${trait.name}"]`);
                if (slider) {
                    formData.personality[trait.name] = parseInt(slider.value);
                }
            });
            break;

        default:
            if (step.fields) {
                step.fields.forEach(field => {
                    const input = currentStepEl.querySelector(`[name="${field.name}"]`);
                    if (input && input.type !== 'file') {
                        formData[field.name] = input.value;
                    }
                });
            }
            if (step.colors) {
                step.colors.forEach(color => {
                    const input = currentStepEl.querySelector(`input[name="${color.name}"]`);
                    if (input) {
                        formData.colors[color.name] = input.value;
                    }
                });
            }
    }
}

function collectAllData() {
    // Save the last step
    saveStepData(currentStep);

    // Also collect any unsaved data
    ONBOARDING_STEPS.forEach((step, index) => {
        const currentStepEl = document.querySelector(`.form-step[data-step="${index}"]`);
        if (!currentStepEl) return;

        if (step.fields) {
            step.fields.forEach(field => {
                if (!formData[field.name]) {
                    const input = currentStepEl.querySelector(`[name="${field.name}"]`);
                    if (input && input.type !== 'file') {
                        formData[field.name] = input.value;
                    }
                }
            });
        }
    });

    return formData;
}

// ===== Form Submission =====

async function handleSubmit(e) {
    e.preventDefault();

    if (!validateStep(currentStep)) {
        return;
    }

    const data = collectAllData();

    // Store onboarding data for later use during payment
    onboardingData = data;

    // Show loading
    loadingOverlay.classList.add('active');

    try {
        // Validate onboarding data (don't create agent yet, just validate)
        const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000'
            : 'https://ai-realtor.fly.dev';

        const response = await fetch(`${API_URL}/onboarding/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error('Failed to validate onboarding data');
        }

        const result = await response.json();

        // Hide loading, show success modal with pricing button
        loadingOverlay.classList.remove('active');

        // Update success modal
        document.getElementById('assistantName').textContent = data.assistant_name || 'Your AI Assistant';
        document.getElementById('assistantTagline').textContent = `Powered by ${data.assistant_style || 'AI'}`;

        successModal.classList.add('active');

    } catch (error) {
        loadingOverlay.classList.remove('active');
        alert('There was an error validating your information. Please try again.');
        console.error('Error:', error);
    }
}

// Store onboarding data for later use
let onboardingData = null;

// ===== Pricing & Payment Flow =====

function showPricingOptions() {
    successModal.classList.remove('active');
    document.getElementById('pricingModal').classList.add('active');
}

function closePricingModal() {
    document.getElementById('pricingModal').classList.remove('active');
}

function selectPlan(plan) {
    const planConfig = {
        starter: {
            name: 'Starter Plan',
            price: '$99',
            period: 'One-time payment'
        },
        professional: {
            name: 'Professional Plan',
            price: '$299',
            period: 'One-time payment'
        },
        enterprise: {
            name: 'Enterprise Plan',
            price: '$500',
            period: 'Per year'
        }
    };

    const config = planConfig[plan];

    // Update payment modal
    document.getElementById('paymentPlanName').textContent = config.name;
    document.getElementById('paymentPlanPrice').textContent = config.price;
    document.getElementById('paymentPlanPeriod').textContent = config.period;

    // Store selected plan
    window.selectedPlan = plan;

    // Show payment modal
    document.getElementById('pricingModal').classList.remove('active');
    document.getElementById('paymentModal').classList.add('active');
}

function closePaymentModal() {
    document.getElementById('paymentModal').classList.remove('active');
}

async function processStripePayment() {
    const planPrices = {
        starter: 99,
        professional: 299,
        enterprise: 500
    };

    const plan = window.selectedPlan;
    const price = planPrices[plan];

    // Show loading
    const paymentModal = document.getElementById('paymentModal');
    const originalContent = paymentModal.innerHTML;
    paymentModal.innerHTML = `
        <div class="payment-modal-content" style="padding: 3rem; text-align: center;">
            <div class="loading-spinner" style="margin: 0 auto 1.5rem;"></div>
            <h3>Processing Payment...</h3>
            <p>Redirecting to Stripe secure checkout</p>
        </div>
    `;

    try {
        // Call backend to create Stripe Checkout Session and agent
        const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000'
            : 'https://ai-realtor.fly.dev';

        const response = await fetch(`${API_URL}/onboarding/create-agent-and-payment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                onboarding_data: onboardingData,
                plan: plan,
                price: price
            })
        });

        if (!response.ok) {
            throw new Error('Failed to process payment');
        }

        const result = await response.json();

        // Redirect to Stripe Checkout
        if (result.checkout_url) {
            window.location.href = result.checkout_url;
        } else if (result.magic_link) {
            // Payment already processed, show magic link directly
            showMagicLink(result.magic_link, result.expires_at);
        } else {
            throw new Error('No checkout URL returned');
        }

    } catch (error) {
        console.error('Payment error:', error);

        // Show error and allow retry
        paymentModal.innerHTML = `
            <div class="payment-modal-content" style="padding: 3rem; text-align: center;">
                <div style="width: 80px; height: 80px; margin: 0 auto 1.5rem; background: rgba(239, 68, 68, 0.1); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #ef4444;">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                </div>
                <h3>Payment Failed</h3>
                <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">There was an error processing your payment. Please try again.</p>
                <button class="btn btn-primary" onclick="location.reload()">Try Again</button>
            </div>
        `;
    }
}

function showMagicLink(magicLink, expiresAt) {
    // Hide payment modal
    document.getElementById('paymentModal').classList.remove('active');

    // Set magic link
    document.getElementById('magicLinkInput').value = magicLink;

    // Calculate and display expiry date
    const expiryDate = new Date(expiresAt);
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    document.getElementById('linkExpiryDate').textContent = expiryDate.toLocaleDateString('en-US', options);

    // Show magic link modal
    document.getElementById('magicLinkModal').classList.add('active');

    // Auto-copy to clipboard
    copyMagicLink();
}

function copyMagicLink() {
    const magicLinkInput = document.getElementById('magicLinkInput');
    const copyBtn = document.querySelector('.copy-btn');

    magicLinkInput.select();
    document.execCommand('copy');

    // Show feedback
    const originalHTML = copyBtn.innerHTML;
    copyBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20,6 9,17 4,12"/>
        </svg>
        Copied!
    `;

    setTimeout(() => {
        copyBtn.innerHTML = originalHTML;
    }, 2000);
}

function openMagicLink() {
    const magicLink = document.getElementById('magicLinkInput').value;
    window.open(magicLink, '_blank');
}

function bookmarkLink() {
    alert('Press Ctrl+D (Windows) or Cmd+D (Mac) to bookmark this page for easy access to your tracking link.');
}

// ===== Check for Payment Return =====

function checkPaymentReturn() {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    const success = urlParams.get('success');

    if (sessionId && success === 'true') {
        // Payment successful, fetch magic link
        fetchMagicLink(sessionId);
    } else if (success === 'false') {
        // Payment cancelled or failed
        alert('Payment was cancelled. Please try again when you\'re ready.');
    }
}

async function fetchMagicLink(sessionId) {
    try {
        const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000'
            : 'https://ai-realtor.fly.dev';

        const response = await fetch(`${API_URL}/onboarding/payment-success?session_id=${sessionId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch magic link');
        }

        const result = await response.json();
        showMagicLink(result.magic_link, result.expires_at);

        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);

    } catch (error) {
        console.error('Error fetching magic link:', error);
        alert('There was an error processing your payment. Please contact support.');
    }
}

// ===== Initialize =====

document.addEventListener('DOMContentLoaded', init);
