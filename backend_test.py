#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Backlink Builder
Tests all authentication, CRUD operations, and feature endpoints
"""

import requests
import sys
import json
from datetime import datetime

class BacklinkBuilderAPITester:
    def __init__(self, base_url="https://high-da-links.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test_result(self, test_name, success, details=""):
        """Log test results for reporting"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED: {details}")
        
        self.tests_run += 1

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test with detailed error handling"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)
            else:
                self.log_test_result(name, False, f"Unsupported method: {method}")
                return False, {}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json() if response.text else {}
            except:
                response_data = {"text": response.text}

            details = f"Status: {response.status_code}"
            if not success:
                details += f" (Expected: {expected_status}), Response: {response.text[:200]}"

            self.log_test_result(name, success, details)
            return success, response_data

        except Exception as e:
            self.log_test_result(name, False, f"Request failed: {str(e)}")
            return False, {}

    # ============= AUTHENTICATION TESTS =============
    
    def test_register_user(self):
        """Test user registration"""
        user_data = {
            "email": "test@linkbuilder.com",
            "password": "Test123!",
            "name": "Test User"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register", 
            200,
            data=user_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_login_user(self):
        """Test user login - fallback if registration fails"""
        login_data = {
            "email": "test@linkbuilder.com", 
            "password": "Test123!"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST", 
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_get_user_profile(self):
        """Test getting current user profile"""
        if not self.token:
            self.log_test_result("Get User Profile", False, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "auth/me",
            200
        )
        return success

    # ============= DASHBOARD TESTS =============
    
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        if not self.token:
            self.log_test_result("Dashboard Stats", False, "No auth token available") 
            return False
            
        success, response = self.run_test(
            "Dashboard Stats",
            "GET", 
            "dashboard/stats",
            200
        )
        return success

    # ============= GUEST POSTS TESTS =============
    
    def test_guest_post_search(self):
        """Test guest post search functionality"""
        if not self.token:
            self.log_test_result("Guest Post Search", False, "No auth token available")
            return False
            
        search_data = {
            "query": "digital marketing",
            "niche": "marketing", 
            "max_results": 10
        }
        
        success, response = self.run_test(
            "Guest Post Search",
            "POST",
            "guest-posts/search",
            200,
            data=search_data
        )
        
        if success and 'results' in response:
            return len(response['results']) >= 0  # Accept empty results
        return success

    def test_get_guest_posts(self):
        """Test retrieving guest posts"""
        if not self.token:
            self.log_test_result("Get Guest Posts", False, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Get Guest Posts",
            "GET", 
            "guest-posts",
            200
        )
        return success

    # ============= BROKEN LINKS TESTS =============
    
    def test_broken_link_scan(self):
        """Test broken link scanning"""
        if not self.token:
            self.log_test_result("Broken Link Scan", False, "No auth token available")
            return False
            
        scan_data = {
            "url": "https://example.com",
            "max_depth": 1
        }
        
        success, response = self.run_test(
            "Broken Link Scan", 
            "POST",
            "broken-links/scan",
            200,
            data=scan_data
        )
        return success

    def test_get_broken_links(self):
        """Test retrieving broken links"""
        if not self.token:
            self.log_test_result("Get Broken Links", False, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Get Broken Links",
            "GET",
            "broken-links", 
            200
        )
        return success

    # ============= COMPETITOR TESTS =============
    
    def test_competitor_analysis(self):
        """Test competitor backlink analysis"""
        if not self.token:
            self.log_test_result("Competitor Analysis", False, "No auth token available")
            return False
            
        analysis_data = {
            "domain": "competitor.com",
            "max_results": 20
        }
        
        success, response = self.run_test(
            "Competitor Analysis",
            "POST", 
            "competitors/analyze",
            200,
            data=analysis_data
        )
        return success

    def test_get_competitor_backlinks(self):
        """Test retrieving competitor backlinks"""
        if not self.token:
            self.log_test_result("Get Competitor Backlinks", False, "No auth token available") 
            return False
            
        success, response = self.run_test(
            "Get Competitor Backlinks",
            "GET",
            "competitors",
            200
        )
        return success

    # ============= DIRECTORIES TESTS =============
    
    def test_directories_seed(self):
        """Test seeding directories with defaults"""
        if not self.token:
            self.log_test_result("Directories Seed", False, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Directories Seed",
            "POST",
            "directories/seed", 
            200
        )
        return success

    def test_get_directories(self):
        """Test retrieving directories"""
        if not self.token:
            self.log_test_result("Get Directories", False, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Get Directories",
            "GET",
            "directories",
            200
        )
        return success

    def test_add_directory(self):
        """Test adding a new directory"""
        if not self.token:
            self.log_test_result("Add Directory", False, "No auth token available")
            return False
            
        directory_data = {
            "name": "Test Directory",
            "url": "https://testdirectory.com",
            "da_score": 65,
            "category": "General",
            "submission_status": "pending"
        }
        
        success, response = self.run_test(
            "Add Directory",
            "POST",
            "directories",
            200,
            data=directory_data
        )
        return success

    # ============= OUTREACH TESTS =============
    
    def test_seed_email_templates(self):
        """Test seeding default email templates"""
        if not self.token:
            self.log_test_result("Seed Email Templates", False, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Seed Email Templates",
            "POST",
            "outreach/templates/seed",
            200
        )
        return success

    def test_get_email_templates(self):
        """Test retrieving email templates"""
        if not self.token:
            self.log_test_result("Get Email Templates", False, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Get Email Templates",
            "GET", 
            "outreach/templates",
            200
        )
        return success

    def test_send_outreach_email(self):
        """Test sending outreach email (expected to fail due to SendGrid config)"""
        if not self.token:
            self.log_test_result("Send Outreach Email", False, "No auth token available")
            return False
            
        email_data = {
            "to_email": "test@example.com",
            "subject": "Test Outreach Email", 
            "body": "This is a test email for backlink building."
        }
        
        success, response = self.run_test(
            "Send Outreach Email", 
            "POST",
            "outreach/send",
            200,
            data=email_data
        )
        
        # Note: This is expected to succeed with API call but email will fail due to SendGrid config
        return success

    def test_get_outreach_emails(self):
        """Test retrieving sent outreach emails"""
        if not self.token:
            self.log_test_result("Get Outreach Emails", False, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Get Outreach Emails",
            "GET",
            "outreach/emails", 
            200
        )
        return success

    # ============= SETTINGS TESTS =============
    
    def test_get_settings(self):
        """Test retrieving user settings"""
        if not self.token:
            self.log_test_result("Get Settings", False, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Get Settings",
            "GET",
            "settings",
            200
        )
        return success

    def test_update_settings(self):
        """Test updating user settings"""
        if not self.token:
            self.log_test_result("Update Settings", False, "No auth token available")
            return False
            
        settings_data = {
            "your_name": "Updated Test User",
            "your_website": "https://testsite.com",
            "default_niche": "Digital Marketing"
        }
        
        success, response = self.run_test(
            "Update Settings",
            "PUT", 
            "settings",
            200,
            data=settings_data
        )
        return success

    # ============= ROOT ENDPOINT TEST =============
    
    def test_api_root(self):
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        return success

def main():
    """Main test execution"""
    print("🚀 Starting Backlink Builder API Tests...")
    print(f"Backend URL: https://high-da-links.preview.emergentagent.com")
    print("=" * 60)
    
    tester = BacklinkBuilderAPITester()
    
    # Test API availability first
    if not tester.test_api_root():
        print("❌ API is not accessible. Exiting...")
        return 1
    
    # Authentication Tests
    print("\n📝 Testing Authentication...")
    auth_success = False
    
    # Try registration first, fallback to login
    if tester.test_register_user() or tester.test_login_user():
        auth_success = True
        tester.test_get_user_profile()
    
    if not auth_success:
        print("❌ Authentication failed. Cannot proceed with protected endpoints.")
        return 1
    
    # Dashboard Tests
    print("\n📊 Testing Dashboard...")
    tester.test_dashboard_stats()
    
    # Feature Tests
    print("\n🔍 Testing Guest Posts...")
    tester.test_guest_post_search()
    tester.test_get_guest_posts()
    
    print("\n🔗 Testing Broken Links...")
    tester.test_broken_link_scan()
    tester.test_get_broken_links()
    
    print("\n📈 Testing Competitor Analysis...")
    tester.test_competitor_analysis()
    tester.test_get_competitor_backlinks()
    
    print("\n📁 Testing Directories...")
    tester.test_directories_seed()
    tester.test_get_directories()
    tester.test_add_directory()
    
    print("\n✉️ Testing Outreach...")
    tester.test_seed_email_templates()
    tester.test_get_email_templates()
    tester.test_send_outreach_email()  # Expected to fail gracefully
    tester.test_get_outreach_emails()
    
    print("\n⚙️ Testing Settings...")
    tester.test_get_settings()
    tester.test_update_settings()
    
    # Results Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        
        # Show failed tests
        print("\nFailed Tests:")
        for result in tester.test_results:
            if not result['success']:
                print(f"  ❌ {result['test']}: {result['details']}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())