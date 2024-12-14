import launch

if not launch.is_installed("requests"):
    launch.run_pip("install requests", "requirements for perchance")

if not launch.is_installed("python-dotenv"):
    launch.run_pip("install python-dotenv", "requirements for perchance")
