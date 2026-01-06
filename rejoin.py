import time
import subprocess
import sys
import requests
from datetime import datetime

class RobloxAutoRejoin:
    def __init__(self):
        self.session = requests.Session()
        self.username = None
        self.check_interval = 30  # Kiểm tra mỗi 30 giây
        
    def check_adb(self):
        """Kiểm tra ADB"""
        try:
            result = subprocess.run(['adb', 'devices'], 
                                  capture_output=True, text=True)
            devices = [line for line in result.stdout.split('\n') 
                      if '\tdevice' in line]
            return len(devices) > 0
        except:
            return False
    
    def get_user_presence(self, username):
        """Kiểm tra trạng thái online/offline của user"""
        try:
            # API lấy User ID
            url = f"https://users.roblox.com/v1/users/search?keyword={username}&limit=1"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None, "API Error"
            
            data = response.json()
            if not data.get('data'):
                return None, "User không tồn tại"
            
            user_id = data['data'][0]['id']
            display_name = data['data'][0]['displayName']
            
            # API kiểm tra presence
            presence_url = f"https://presence.roblox.com/v1/presence/users"
            payload = {"userIds": [user_id]}
            presence_response = self.session.post(presence_url, 
                                                 json=payload, timeout=10)
            
            if presence_response.status_code == 200:
                presence_data = presence_response.json()
                if presence_data.get('userPresences'):
                    user_presence = presence_data['userPresences'][0]
                    status = user_presence.get('userPresenceType', 0)
                    
                    status_map = {
                        0: "Offline",
                        1: "Online - Website",
                        2: "Online - In Game",
                        3: "Online - Studio"
                    }
                    
                    return {
                        'user_id': user_id,
                        'username': username,
                        'display_name': display_name,
                        'status': status_map.get(status, "Unknown"),
                        'status_code': status,
                        'last_online': user_presence.get('lastOnline', 'N/A')
                    }, None
            
            return None, "Không thể lấy presence"
            
        except Exception as e:
            return None, str(e)
    
    def check_disconnect_screen(self):
        """Kiểm tra màn hình disconnect bằng OCR/UI"""
        try:
            # Chụp màn hình
            subprocess.run(['adb', 'shell', 'screencap', 
                          '/sdcard/screen.png'], check=True)
            subprocess.run(['adb', 'pull', '/sdcard/screen.png', 
                          '/sdcard/'], check=True)
            
            # Kiểm tra text "Disconnected" hoặc "Lost connection"
            result = subprocess.run(['adb', 'shell', 'dumpsys', 'window'],
                                  capture_output=True, text=True)
            
            # Tìm các dấu hiệu disconnect
            keywords = ['disconnect', 'lost connection', 'error', 
                       'rejoin', 'connection lost']
            text_lower = result.stdout.lower()
            
            for keyword in keywords:
                if keyword in text_lower:
                    return True
            
            return False
        except:
            return False
    
    def check_roblox_running(self):
        """Kiểm tra Roblox có đang chạy không"""
        try:
            result = subprocess.run([
                'adb', 'shell', 'pidof', 'com.roblox.client'
            ], capture_output=True, text=True)
            return bool(result.stdout.strip())
        except:
            return False
    
    def force_stop_roblox(self):
        """Dừng Roblox"""
        try:
            print("⏹️  Đang dừng Roblox...")
            subprocess.run(['adb', 'shell', 'am', 'force-stop', 
                          'com.roblox.client'], check=True)
            time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return False
    
    def open_roblox(self):
        """Mở Roblox"""
        try:
            print("🚀 Đang mở Roblox...")
            subprocess.run([
                'adb', 'shell', 'am', 'start',
                '-n', 'com.roblox.client/com.roblox.client.startup.ActivitySplash'
            ], check=True)
            time.sleep(5)
            return True
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return False
    
    def rejoin(self):
        """Thực hiện rejoin"""
        print("\n🔄 Đang rejoin...")
        if self.force_stop_roblox():
            if self.open_roblox():
                print("✅ Rejoin thành công!")
                return True
        print("❌ Rejoin thất bại!")
        return False
    
    def monitor_and_rejoin(self):
        """Giám sát và tự động rejoin khi disconnect"""
        print("\n=== CHẾ ĐỘ MONITOR & AUTO REJOIN ===")
        print(f"Kiểm tra mỗi {self.check_interval} giây")
        print("Nhấn Ctrl+C để dừng\n")
        
        disconnect_count = 0
        
        try:
            while True:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Đang kiểm tra...", end=" ")
                
                # Kiểm tra Roblox có chạy không
                if not self.check_roblox_running():
                    print("⚠️  Roblox không chạy!")
                    print("Đang mở lại Roblox...")
                    self.open_roblox()
                    time.sleep(self.check_interval)
                    continue
                
                # Kiểm tra disconnect
                if self.check_disconnect_screen():
                    disconnect_count += 1
                    print(f"❌ Phát hiện disconnect! (Lần {disconnect_count})")
                    self.rejoin()
                else:
                    print("✅ OK")
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Đã dừng monitor.")
    
    def check_account_status(self):
        """Kiểm tra trạng thái account"""
        print("\n=== KIỂM TRA TRẠNG THÁI ACCOUNT ===\n")
        
        username = input("Nhập Roblox username: ").strip()
        
        print(f"\n🔍 Đang kiểm tra user: {username}...")
        
        result, error = self.get_user_presence(username)
        
        if error:
            print(f"❌ Lỗi: {error}")
            return
        
        print("\n📊 Thông tin account:")
        print(f"  • Username: {result['username']}")
        print(f"  • Display Name: {result['display_name']}")
        print(f"  • User ID: {result['user_id']}")
        print(f"  • Trạng thái: {result['status']}")
        
        if result['status_code'] == 0:
            print(f"  • Lần online cuối: {result['last_online']}")
        
        # Hỏi có muốn monitor không
        if result['status_code'] == 2:  # In Game
            choice = input("\n🎮 User đang in-game. Monitor account này? (y/n): ")
            if choice.lower() == 'y':
                self.username = username
                self.monitor_account()
    
    def monitor_account(self):
        """Monitor trạng thái account liên tục"""
        if not self.username:
            print("❌ Chưa set username!")
            return
        
        print(f"\n=== MONITOR ACCOUNT: {self.username} ===")
        print("Nhấn Ctrl+C để dừng\n")
        
        try:
            while True:
                timestamp = datetime.now().strftime("%H:%M:%S")
                result, error = self.get_user_presence(self.username)
                
                if error:
                    print(f"[{timestamp}] ❌ Lỗi: {error}")
                else:
                    status = result['status']
                    icon = "🟢" if result['status_code'] > 0 else "🔴"
                    print(f"[{timestamp}] {icon} {status}")
                    
                    # Nếu offline, thử rejoin
                    if result['status_code'] == 0:
                        print("⚠️  Account offline! Thử rejoin...")
                        self.rejoin()
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Đã dừng monitor.")

def main():
    bot = RobloxAutoRejoin()
    
    print("=" * 50)
    print("     ROBLOX AUTO REJOIN & MONITOR")
    print("=" * 50)
    
    # Kiểm tra ADB
    if not bot.check_adb():
        print("\n❌ Không tìm thấy ADB device!")
        print("\n📋 Hướng dẫn:")
        print("1. pkg install android-tools")
        print("2. Bật Developer Options & USB Debugging")
        print("3. adb connect 127.0.0.1:5555")
        print("4. adb devices (kiểm tra)")
        sys.exit(1)
    
    print("\n✅ ADB đã kết nối")
    
    print("\n📋 MENU:")
    print("1. Rejoin 1 lần")
    print("2. Monitor & Auto rejoin khi disconnect")
    print("3. Check trạng thái account (Online/Offline)")
    print("4. Monitor account liên tục")
    
    try:
        choice = input("\nChọn chức năng (1-4): ").strip()
        
        if choice == "1":
            bot.rejoin()
        elif choice == "2":
            interval = input(f"Khoảng thời gian check (giây, mặc định {bot.check_interval}): ")
            if interval.isdigit():
                bot.check_interval = int(interval)
            bot.monitor_and_rejoin()
        elif choice == "3":
            bot.check_account_status()
        elif choice == "4":
            username = input("Nhập username cần monitor: ").strip()
            bot.username = username
            interval = input(f"Khoảng thời gian check (giây, mặc định {bot.check_interval}): ")
            if interval.isdigit():
                bot.check_interval = int(interval)
            bot.monitor_account()
        else:
            print("❌ Lựa chọn không hợp lệ!")
            
    except KeyboardInterrupt:
        print("\n\n👋 Tạm biệt!")

if __name__ == "__main__":
    main()
