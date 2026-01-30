/**
 * Multi-Language System for Rural Healthcare Platform
 * Supports: English (en), Hindi (hi), Marathi (mr)
 * 
 * Usage:
 * 1. Include this file in all HTML pages: <script src="/js/i18n.js"></script>
 * 2. Add data-i18n attributes to elements: <h1 data-i18n="welcome">Welcome</h1>
 * 3. Call initLanguage() on page load
 */

// Translation dictionary
const translations = {
    en: {
        // Navigation & Common
        'language': 'Language',
        'home': 'Home',
        'about': 'About',
        'services': 'Services',
        'login': 'Login',
        'register': 'Register',
        'logout': 'Logout',
        'dashboard': 'Dashboard',
        'back': 'Back',
        'save': 'Save',
        'cancel': 'Cancel',
        'submit': 'Submit',
        'close': 'Close',
        'search': 'Search',
        'loading': 'Loading...',
        
        // Landing Page
        'hero_title': 'Your Health,',
        'hero_subtitle': 'In Your Voice.',
        'hero_desc': 'Digital healthcare records for rural India. Speak your symptoms, AI understands.',
        'get_started': 'Get Started',
        'learn_more': 'Learn More',
        'for_patients': 'For Patients',
        'for_doctors': 'For Doctors',
        'for_labs': 'For Labs',
        'try_voice_booking': 'Try AI Voice Booking:',
        'start_speaking': 'Start Speaking',
        'platform_ecosystem': 'Our Platform Ecosystem',
        'platform_desc': 'Direct portals designed for Patients, Doctors, and Labs.',
        'patient_portal': 'Patient Portal',
        'patient_portal_desc': 'Book appointments, view lab reports, and consult doctors online with multilingual support.',
        'doctor_desk': "Doctor's Desk",
        'doctor_desk_desc': 'Secure portal for clinicians to track patient trends and pathology data instantly.',
        'lab_hub': 'Lab Technician Hub',
        'lab_hub_desc': 'Advanced tools for laboratory technicians to manage rural sample collection logistics.',
        'access_portal': 'Access Portal',
        'empowering_clinical': 'Empowering Clinical Decisions',
        'empowering_desc': 'We provide doctors with a unified dashboard to track patient history and diagnostic progress across 500+ rural locations.',
        'multilingual_reports': 'Multilingual Reports',
        'ai_trends': 'AI-Integrated Trends',
        'advanced_lab': 'Advanced Lab Logistics',
        'advanced_lab_desc': 'Our platform streamlines the connection between rural collection centers and high-end diagnostic hubs through automated GPS tracking.',
        'optimized_transport': 'Optimized sample transportation with temperature monitoring.',
        'copyright': '© 2026 Health Nova. Quality Healthcare Access For All.',
        
        // Login/Register
        'phone_number': 'Phone Number',
        'password': 'Password',
        'full_name': 'Full Name',
        'email': 'Email (Optional)',
        'role': 'I am a',
        'patient': 'Patient',
        'doctor': 'Doctor',
        'lab_tech': 'Lab Technician',
        'login_title': 'Welcome Back',
        'register_title': 'Create Account',
        'already_account': 'Already have an account?',
        'no_account': "Don't have an account?",
        
        // Dashboard
        'welcome': 'Welcome',
        'appointments': 'Appointments',
        'medical_records': 'Medical Records',
        'prescriptions': 'Prescriptions',
        'lab_reports': 'Lab Reports',
        'book_appointment': 'Book Appointment',
        'ai_assistant': 'AI Assistant',
        'health_assistant': 'Health Assistant',
        'clinical_assistant': 'Clinical Assistant',
        'profile': 'Profile',
        'settings': 'Settings',
        
        // Appointments
        'upcoming_appointments': 'Upcoming Appointments',
        'past_appointments': 'Past Appointments',
        'appointment_date': 'Appointment Date',
        'doctor_name': 'Doctor Name',
        'reason': 'Reason',
        'status': 'Status',
        'join_video': 'Join Video Call',
        'scheduled': 'Scheduled',
        'completed': 'Completed',
        'cancelled': 'Cancelled',
        
        // Booking
        'book_consultation': 'Book Consultation',
        'select_doctor': 'Select Doctor',
        'select_date': 'Select Date',
        'select_time': 'Select Time',
        'reason_for_visit': 'Reason for Visit',
        'confirm_booking': 'Confirm Booking',
        'book_now': 'Book Now',
        
        // Chatbot
        'type_message': 'Type your message...',
        'send': 'Send',
        'ai_response': 'AI Response',
        'disclaimer': 'I provide health education only. I cannot diagnose or prescribe.',
        
        // Profile
        'personal_info': 'Personal Information',
        'age': 'Age',
        'gender': 'Gender',
        'blood_group': 'Blood Group',
        'address': 'Address',
        'emergency_contact': 'Emergency Contact',
        'medical_history': 'Medical History',
        'allergies': 'Allergies',
        'chronic_conditions': 'Chronic Conditions',
        'update_profile': 'Update Profile',
        
        // Messages
        'success': 'Success!',
        'error': 'Error',
        'booking_success': 'Appointment booked successfully',
        'booking_error': 'Failed to book appointment',
        'login_success': 'Login successful',
        'login_error': 'Invalid credentials',
        'register_success': 'Registration successful',
        'register_error': 'Registration failed',
        
        // Login/Register Forms
        'login_title': 'Welcome Back',
        'register_title': 'Create Account',
        'phone_number': 'Phone Number',
        'email': 'Email',
        'full_name': 'Full Name',
        'password': 'Password',
        'confirm_password': 'Confirm Password',
        'role': 'Role',
        'patient': 'Patient',
        'doctor': 'Doctor',
        'lab_tech': 'Lab Technician',
        'forgot_password': 'Forgot Password?',
        'create_account': 'Create Account',
        'already_account': 'Already have an account?',
        'signin': 'Sign In',
        
        // Dashboard Common
        'welcome': 'Welcome',
        'upcoming_appointments': 'Upcoming Appointments',
        'past_appointments': 'Past Appointments',
        'medical_records': 'Medical Records',
        'lab_reports': 'Lab Reports',
        'prescriptions': 'Prescriptions',
        'total_visits': 'Total Visits',
        'pending': 'Pending',
        'view_details': 'View Details',
        'download': 'Download',
        'edit': 'Edit',
        'delete': 'Delete',
        'view': 'View',
        'no_appointments': 'No appointments scheduled',
        'no_records': 'No records found',
        
        // Doctor Dashboard
        'patients': 'Patients',
        'consultations': 'Consultations',
        'prescribe': 'Prescribe',
        'order_tests': 'Order Tests',
        'view_patient': 'View Patient',
        'patient_name': 'Patient Name',
        'last_visit': 'Last Visit',
        'next_appointment': 'Next Appointment',
        
        // Booking Details
        'doctor_name': 'Doctor Name',
        'specialization': 'Specialization',
        'experience': 'Experience',
        'consultation_fee': 'Consultation Fee',
        'available_times': 'Available Times',
        'appointment_details': 'Appointment Details',
        'date': 'Date',
        'time': 'Time',
        'reason': 'Reason',
        'status': 'Status',
        
        // Dashboard Cards & Actions
        'add_symptoms': 'Add Symptoms',
        'view_reports': 'View Reports',
        'view_all': 'View All',
        'add_now': 'Add Now',
        'check_status': 'Check Status',
        'my_appointments': 'My Appointments',
        'date_time': 'Date & Time',
        'action': 'Action',
    },
    
    hi: {
        // Navigation & Common
        'language': 'भाषा',
        'home': 'होम',
        'about': 'के बारे में',
        'services': 'सेवाएं',
        'login': 'लॉगिन',
        'register': 'रजिस्टर करें',
        'logout': 'लॉगआउट',
        'dashboard': 'डैशबोर्ड',
        'back': 'वापस',
        'save': 'सेव करें',
        'cancel': 'रद्द करें',
        'submit': 'जमा करें',
        'close': 'बंद करें',
        'search': 'खोजें',
        'loading': 'लोड हो रहा है...',
        
        // Landing Page
        'hero_title': 'आपका स्वास्थ्य,',
        'hero_subtitle': 'आपकी आवाज़ में।',
        'hero_desc': 'ग्रामीण भारत के लिए डिजिटल स्वास्थ्य रिकॉर्ड। अपने लक्षण बोलें, AI समझता है।',
        'get_started': 'शुरू करें',
        'learn_more': 'और जानें',
        'for_patients': 'मरीजों के लिए',
        'for_doctors': 'डॉक्टरों के लिए',
        'for_labs': 'लैब के लिए',
        'try_voice_booking': 'AI वॉइस बुकिंग आज़माएं:',
        'start_speaking': 'बोलना शुरू करें',
        'platform_ecosystem': 'हमारा प्लेटफ़ॉर्म इकोसिस्टम',
        'platform_desc': 'मरीजों, डॉक्टरों और लैब के लिए सीधे पोर्टल।',
        'patient_portal': 'रोगी पोर्टल',
        'patient_portal_desc': 'बहुभाषी समर्थन के साथ अपॉइंटमेंट बुक करें, लैब रिपोर्ट देखें और डॉक्टरों से ऑनलाइन परामर्श करें।',
        'doctor_desk': 'डॉक्टर का डेस्क',
        'doctor_desk_desc': 'चिकित्सकों के लिए रोगी रुझान और पैथोलॉजी डेटा तुरंत ट्रैक करने के लिए सुरक्षित पोर्टल।',
        'lab_hub': 'लैब तकनीशियन हब',
        'lab_hub_desc': 'ग्रामीण नमूना संग्रह रसद प्रबंधित करने के लिए प्रयोगशाला तकनीशियनों के लिए उन्नत उपकरण।',
        'access_portal': 'पोर्टल एक्सेस करें',
        'empowering_clinical': 'क्लिनिकल निर्णयों को सशक्त बनाना',
        'empowering_desc': 'हम डॉक्टरों को 500+ ग्रामीण स्थानों में रोगी इतिहास और निदान प्रगति ट्रैक करने के लिए एकीकृत डैशबोर्ड प्रदान करते हैं।',
        'multilingual_reports': 'बहुभाषी रिपोर्ट',
        'ai_trends': 'AI-एकीकृत ट्रेंड',
        'advanced_lab': 'उन्नत लैब लॉजिस्टिक्स',
        'advanced_lab_desc': 'हमारा प्लेटफ़ॉर्म स्वचालित GPS ट्रैकिंग के माध्यम से ग्रामीण संग्रह केंद्रों और उच्च-स्तरीय निदान केंद्रों के बीच संबंध को सरल बनाता है।',
        'optimized_transport': 'तापमान निगरानी के साथ नमूना परिवहन का अनुकूलन।',
        'copyright': '© 2026 हेल्थ नोवा। सभी के लिए गुणवत्तापूर्ण स्वास्थ्य सेवा।',
        
        // Login/Register
        'phone_number': 'फोन नंबर',
        'password': 'पासवर्ड',
        'full_name': 'पूरा नाम',
        'email': 'ईमेल (वैकल्पिक)',
        'role': 'मैं हूँ',
        'patient': 'मरीज',
        'doctor': 'डॉक्टर',
        'lab_tech': 'लैब तकनीशियन',
        'login_title': 'वापस स्वागत है',
        'register_title': 'खाता बनाएं',
        'already_account': 'पहले से खाता है?',
        'no_account': 'खाता नहीं है?',
        
        // Dashboard
        'welcome': 'स्वागत है',
        'appointments': 'अपॉइंटमेंट',
        'medical_records': 'मेडिकल रिकॉर्ड',
        'prescriptions': 'प्रिस्क्रिप्शन',
        'lab_reports': 'लैब रिपोर्ट',
        'book_appointment': 'अपॉइंटमेंट बुक करें',
        'ai_assistant': 'AI सहायक',
        'health_assistant': 'स्वास्थ्य सहायक',
        'clinical_assistant': 'क्लिनिकल सहायक',
        'profile': 'प्रोफाइल',
        'settings': 'सेटिंग्स',
        
        // Appointments
        'upcoming_appointments': 'आगामी अपॉइंटमेंट',
        'past_appointments': 'पिछले अपॉइंटमेंट',
        'appointment_date': 'अपॉइंटमेंट तारीख',
        'doctor_name': 'डॉक्टर का नाम',
        'reason': 'कारण',
        'status': 'स्थिति',
        'join_video': 'वीडियो कॉल जॉइन करें',
        'scheduled': 'निर्धारित',
        'completed': 'पूर्ण',
        'cancelled': 'रद्द',
        
        // Booking
        'book_consultation': 'परामर्श बुक करें',
        'select_doctor': 'डॉक्टर चुनें',
        'select_date': 'तारीख चुनें',
        'select_time': 'समय चुनें',
        'reason_for_visit': 'मिलने का कारण',
        'confirm_booking': 'बुकिंग कन्फर्म करें',
        'book_now': 'अभी बुक करें',
        
        // Chatbot
        'type_message': 'अपना संदेश लिखें...',
        'send': 'भेजें',
        'ai_response': 'AI उत्तर',
        'disclaimer': 'मैं केवल स्वास्थ्य शिक्षा प्रदान करता हूं। मैं निदान या दवा नहीं दे सकता।',
        
        // Profile
        'personal_info': 'व्यक्तिगत जानकारी',
        'age': 'उम्र',
        'gender': 'लिंग',
        'blood_group': 'रक्त समूह',
        'address': 'पता',
        'emergency_contact': 'आपातकालीन संपर्क',
        'medical_history': 'चिकित्सा इतिहास',
        'allergies': 'एलर्जी',
        'chronic_conditions': 'पुरानी बीमारियाँ',
        'update_profile': 'प्रोफाइल अपडेट करें',
        
        // Messages
        'success': 'सफलता!',
        'error': 'त्रुटि',
        'booking_success': 'अपॉइंटमेंट सफलतापूर्वक बुक हुआ',
        'booking_error': 'अपॉइंटमेंट बुक नहीं हो सका',
        'login_success': 'लॉगिन सफल',
        'login_error': 'गलत विवरण',
        'register_success': 'रजिस्ट्रेशन सफल',
        'register_error': 'रजिस्ट्रेशन विफल',
        'update_success': 'अपडेट सफल',
        'confirm_password': 'पासवर्ड पुष्टि',
        'forgot_password': 'पासवर्ड भूल गए?',
        'create_account': 'खाता बनाएं',
        'signin': 'साइन इन',
        'total_visits': 'कुल विज़िट',
        'pending': 'लंबित',
        'view_details': 'विवरण',
        'download': 'डाउनलोड',
        'edit': 'एडिट',
        'delete': 'डिलीट',
        'view': 'देखें',
        'no_appointments': 'कोई अपॉइंटमेंट नहीं',
        'no_records': 'कोई रिकॉर्ड नहीं',
        'patients': 'रोगी',
        'consultations': 'परामर्श',
        'prescribe': 'प्रिस्क्रिप्शन',
        'order_tests': 'टेस्ट ऑर्डर',
        'view_patient': 'रोगी देखें',
        'patient_name': 'रोगी',
        'last_visit': 'लास्ट विज़िट',
        'next_appointment': 'अगला अपॉइंटमेंट',
        'specialization': 'विशेषज्ञता',
        'experience': 'अनुभव',
        'consultation_fee': 'फीस',
        'available_times': 'समय',
        'appointment_details': 'विवरण',
        'date': 'तारीख',
        'time': 'समय',
        'add_symptoms': 'लक्षण जोड़ें',
        'view_reports': 'रिपोर्ट देखें',
        'view_all': 'सभी देखें',
        'add_now': 'अभी जोड़ें',
        'check_status': 'स्थिति जांचें',
        'my_appointments': 'मेरे अपॉइंटमेंट',
        'date_time': 'तारीख और समय',
        'action': 'कार्रवाई',
    },
    
    mr: {
        // Navigation & Common
        'language': 'भाषा',
        'home': 'होम',
        'about': 'बद्दल',
        'services': 'सेवा',
        'login': 'लॉगिन',
        'register': 'नोंदणी करा',
        'logout': 'लॉगआउट',
        'dashboard': 'डॅशबोर्ड',
        'back': 'मागे',
        'save': 'सेव्ह करा',
        'cancel': 'रद्द करा',
        'submit': 'सबमिट करा',
        'close': 'बंद करा',
        'search': 'शोधा',
        'loading': 'लोड होत आहे...',
        
        // Landing Page
        'hero_title': 'तुमचे आरोग्य,',
        'hero_subtitle': 'तुमच्या आवाजात।',
        'hero_desc': 'ग्रामीण भारतासाठी डिजिटल आरोग्य रेकॉर्ड। तुमची लक्षणे सांगा, AI समजतो।',
        'get_started': 'सुरू करा',
        'learn_more': 'अधिक जाणा',
        'for_patients': 'रुग्णांसाठी',
        'for_doctors': 'डॉक्टरांसाठी',
        'for_labs': 'लॅबसाठी',
        'try_voice_booking': 'AI व्हॉइस बुकिंग वापरून पहा:',
        'start_speaking': 'बोलणे सुरू करा',
        'platform_ecosystem': 'आमचे प्लॅटफॉर्
        'empowering_clinical': 'क्लिनिकल निर्णय सशक्त करणे',
        'empowering_desc': 'आम्ही डॉक्टरांना 500+ ग्रामीण ठिकाणांवर रुग्ण इतिहास आणि निदान प्रगती ट्रॅक करण्यासाठी एकीकृत डॅशबोर्ड प्रदान करतो।',
        'multilingual_reports': 'बहुभाषिक अहवाल',
        'ai_trends': 'AI-एकात्मिक ट्रेंड',
        'advanced_lab': 'प्रगत लॅब लॉजिस्टिक्स',
        'advanced_lab_desc': 'आमचे प्लॅटफॉर्म स्वयंचलित GPS ट्रॅकिंगद्वारे ग्रामीण संकलन केंद्रे आणि उच्च-स्तरीय निदान केंद्रांमधील कनेक्शन सुव्यवस्थित करते।',
        'optimized_transport': 'तापमान निरीक्षणासह नमुना वाहतूक अनुकूलित.',
        'copyright': '© 2026 हेल्थ नोवा। सर्वांसाठी गुणवत्तापूर्ण आरोग्य सेवा.',म इकोसिस्टम',
        'platform_desc': 'रुग्ण, डॉक्टर आणि लॅबसाठी थेट पोर्टल.',
        'patient_portal': 'रुग्ण पोर्टल',
        'patient_portal_desc': 'बहुभाषिक समर्थनासह भेटी बुक करा, लॅब अहवाल पहा आणि डॉक्टरांशी ऑनलाइन सल्लामसलत करा।',
        'doctor_desk': 'डॉक्टरांचे डेस्क',
        'doctor_desk_desc': 'रुग्ण ट्रेंड आणि पॅथॉलॉजी डेटा त्वरित ट्रॅक करण्यासाठी चिकित्सकांसाठी सुरक्षित पोर्टल।',
        'lab_hub': 'लॅब तंत्रज्ञ हब',
        'lab_hub_desc': 'ग्रामीण नमुना संकलन लॉजिस्टिक्स व्यवस्थापित करण्यासाठी प्रयोगशाळा तंत्रज्ञांसाठी प्रगत साधने।',
        'access_portal': 'पोर्टल ऍक्सेस करा',
        
        // Login/Register
        'phone_number': 'फोन नंबर',
        'password': 'पासवर्ड',
        'full_name': 'पूर्ण नाव',
        'email': 'ईमेल (पर्यायी)',
        'role': 'मी आहे',
        'patient': 'रुग्ण',
        'doctor': 'डॉक्टर',
        'lab_tech': 'लॅब तंत्रज्ञ',
        'login_title': 'परत स्वागत आहे',
        'register_title': 'खाते तयार करा',
        'already_account': 'आधीच खाते आहे?',
        'no_account': 'खाते नाही?',
        
        // Dashboard
        'welcome': 'स्वागत आहे',
        'appointments': 'भेटी',
        'medical_records': 'वैद्यकीय रेकॉर्ड',
        'prescriptions': 'औषध पत्रिका',
        'lab_reports': 'लॅब अहवाल',
        'book_appointment': 'भेट बुक करा',
        'ai_assistant': 'AI सहाय्यक',
        'health_assistant': 'आरोग्य सहाय्यक',
        'clinical_assistant': 'क्लिनिकल सहाय्यक',
        'profile': 'प्रोफाइल',
        'settings': 'सेटिंग्ज',
        
        // Appointments
        'upcoming_appointments': 'आगामी भेटी',
        'past_appointments': 'मागील भेटी',
        'appointment_date': 'भेटीची तारीख',
        'doctor_name': 'डॉक्टरांचे नाव',
        'reason': 'कारण',
        'status': 'स्थिती',
        'join_video': 'व्हिडिओ कॉल जॉइन करा',
        'scheduled': 'नियोजित',
        'completed': 'पूर्ण',
        'cancelled': 'रद्द',
        
        // Booking
        'book_consultation': 'सल्लामसलत बुक करा',
        'select_doctor': 'डॉक्टर निवडा',
        'select_date': 'तारीख निवडा',
        'select_time': 'वेळ निवडा',
        'reason_for_visit': 'भेटीचे कारण',
        'confirm_booking': 'बुकिंग कन्फर्म करा',
        'book_now': 'आता बुक करा',
        
        // Chatbot
        'type_message': 'तुमचा संदेश टाइप करा...',
        'send': 'पाठवा',
        'ai_response': 'AI उत्तर',
        'disclaimer': 'मी फक्त आरोग्य शिक्षण देतो. मी निदान किंवा औषध देऊ शकत नाही.',
        
        // Profile
        'personal_info': 'वैयक्तिक माहिती',
        'age': 'वय',
        'gender': 'लिंग',
        'blood_group': 'रक्तगट',
        'address': 'पत्ता',
        'emergency_contact': 'आपत्कालीन संपर्क',
        'medical_history': 'वैद्यकीय इतिहास',
        'allergies': 'ऍलर्जी',
        'chronic_conditions': 'जुने आजार',
        'update_profile': 'प्रोफाइल अपडेट करा',
        
        // Messages
        'success': 'यशस्वी!',
        'error': 'त्रुटी',
        'booking_success': 'भेट यशस्वीरित्या बुक झाली',
        'booking_error': 'भेट बुक होऊ शकली नाही',
        'login_success': 'लॉगिन यशस्वी',
        'login_error': 'चुकीची माहिती',
        'register_success': 'नोंदणी यशस्वी',
        'register_error': 'नोंदणी अयशस्वी',
        'update_success': 'अपडेट यशस्वी',
        'confirm_password': 'पासवर्ड पुष्टी',
        'forgot_password': 'पासवर्ड विसरलात?',
        'create_account': 'खाते तयार करा',
        'signin': 'साइन इन',
        'total_visits': 'एकूण भेटी',
        'pending': 'प्रलंबित',
        'view_details': 'तपशील',
        'download': 'डाउनलोड',
        'edit': 'संपादित',
        'delete': 'हटवा',
        'view': 'पहा',
        'no_appointments': 'कोणतीही भेट नाही',
        'no_records': 'रेकॉर्ड आढळले नाहीत',
        'patients': 'रुग्ण',
        'consultations': 'सल्लामसलत',
        'prescribe': 'औषध पत्रिका',
        'order_tests': 'चाचण्या ऑर्डर',
        'view_patient': 'रुग्ण पहा',
        'patient_name': 'रुग्णाचे नाव',
        'last_visit': 'शेवटची भेट',
        'next_appointment': 'पुढील भेट',
        'specialization': 'विशेषीकरण',
        'experience': 'अनुभव',
        'consultation_fee': 'शुल्क',
        'available_times': 'उपलब्ध वेळा',
        'appointment_details': 'भेटीचे तपशील',
        'date': 'तारीख',
        'time': 'वेळ',
        'add_symptoms': 'लक्षणे जोडा',
        'view_reports': 'अहवाल पहा',
        'view_all': 'सर्व पहा',
        'add_now': 'आता जोडा',
        'check_status': 'स्थिती तपासा',
        'my_appointments': 'माझ्या भेटी',
        'date_time': 'तारीख आणि वेळ',
        'action': 'कृती',
    }
};

// Get current language from localStorage or default to 'en'
function getCurrentLanguage() {
    return localStorage.getItem('language') || 'en';
}

// Set language in localStorage
function setLanguage(lang) {
    console.log('[i18n] setLanguage called with:', lang);
    
    if (translations[lang]) {
        console.log('[i18n] Language found in translations, applying...');
        localStorage.setItem('language', lang);
        applyTranslations(lang);
        updateLanguageUI(lang);
        
        // Dispatch custom event for components that need to react
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lang } }));
        console.log('[i18n] Language changed successfully to:', lang);
    } else {
        console.error('[i18n] Language not found:', lang);
    }
}

// Apply translations to all elements with data-i18n attribute
function applyTranslations(lang) {
    const elements = document.querySelectorAll('[data-i18n]');
    
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = translations[lang][key];
        
        if (translation) {
            // Handle different element types
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                if (element.type === 'submit' || element.type === 'button') {
                    element.value = translation;
                } else {
                    element.placeholder = translation;
                }
            } else if (element.tagName === 'SELECT') {
                // Don't translate select elements directly
            } else {
                element.textContent = translation;
            }
        }
    });
    
    // Update HTML lang attribute
    document.documentElement.lang = lang;
}

// Update language dropdown UI
function updateLanguageUI(lang) {
    const languageNames = {
        'en': 'English',
        'hi': 'हिन्दी',
        'mr': 'मराठी'
    };
    
    // Update language dropdown button text
    const langButtons = document.querySelectorAll('.language-dropdown-toggle');
    langButtons.forEach(btn => {
        const icon = btn.querySelector('i');
        if (icon) {
            btn.innerHTML = icon.outerHTML + ' ' + languageNames[lang];
        } else {
            btn.textContent = languageNames[lang];
        }
    });
    
    // Mark active language in dropdowns
    const langLinks = document.querySelectorAll('.language-option');
    langLinks.forEach(link => {
        const linkLang = link.getAttribute('data-lang');
        if (linkLang === lang) {
            link.classList.add('active', 'fw-bold');
        } else {
            link.classList.remove('active', 'fw-bold');
        }
    });
}

// Get translation for a key
function t(key, lang = null) {
    const currentLang = lang || getCurrentLanguage();
    return translations[currentLang][key] || key;
}

// Initialize language system on page load
function initLanguage() {
    const currentLang = getCurrentLanguage();
    console.log('[i18n] Initializing with language:', currentLang);
    
    applyTranslations(currentLang);
    updateLanguageUI(currentLang);
    
    // Setup language switcher click handlers
    const langLinks = document.querySelectorAll('.language-option');
    console.log('[i18n] Found language option links:', langLinks.length);
    
    langLinks.forEach((link, index) => {
        const lang = link.getAttribute('data-lang');
        console.log(`[i18n] Setting up listener ${index + 1} for language:`, lang);
        
        link.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('[i18n] Language clicked:', lang);
            setLanguage(lang);
        });
    });
    
    console.log(`[i18n] Language system initialized. Current language: ${currentLang}`);
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLanguage);
} else {
    initLanguage();
}

// Export for use in other scripts
window.i18n = {
    t,
    setLanguage,
    getCurrentLanguage,
    initLanguage
};
