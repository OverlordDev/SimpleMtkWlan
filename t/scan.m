#import <CoreWLAN/CoreWLAN.h>
int main(void){ @autoreleasepool{
 CWWiFiClient *c=[CWWiFiClient sharedWiFiClient]; CWInterface *i=c.interface;
 printf("iface=%s power=%d ssid=%s bssid=%s ch=%ld\n",i.interfaceName.UTF8String,i.powerOn,i.ssid.UTF8String?:"-",i.bssid.UTF8String?:"-",(long)i.wlanChannel.channelNumber);
 NSError *e=nil; NSTimeInterval t=[NSDate timeIntervalSinceReferenceDate];
 NSSet *s=[i scanForNetworksWithName:nil error:&e];
 printf("scan: %lu networks in %.1fs err=%s\n",(unsigned long)s.count,[NSDate timeIntervalSinceReferenceDate]-t,e.description.UTF8String?:"none");
 for(CWNetwork*n in s) printf("  %s bssid=%s ch=%ld rssi=%ld\n",n.ssid.UTF8String?:"(hidden)",n.bssid.UTF8String?:"-",(long)n.wlanChannel.channelNumber,(long)n.rssiValue);
}return 0;}
