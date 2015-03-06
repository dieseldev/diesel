from diesel import resolve_dns_name, DNSResolutionError
from diesel import Application, Loop, sleep

def resolve_the_google():
    print('started resolution!')
    g_ip = resolve_dns_name("www.google.com")
    print("www.google.com's ip is %s" % g_ip)
    try:
        bad_host = "www.g8asdf21oogle.com"
        print("now checking %s" % bad_host)
        resolve_dns_name(bad_host)
    except DNSResolutionError:
        print("yep, it failed as expected")
    else:
        raise RuntimeError("The bad host resolved.  That's unexpected.")
    g_ip = resolve_dns_name("www.google.com")
    g_ip = resolve_dns_name("www.google.com")
    g_ip = resolve_dns_name("www.google.com")
    g_ip = resolve_dns_name("www.google.com")
    a.halt()

def stuff():
    while True:
        print("doing stuff!")
        sleep(0.01)

a = Application()
a.add_loop(Loop(stuff))
a.add_loop(Loop(resolve_the_google))
a.run()
