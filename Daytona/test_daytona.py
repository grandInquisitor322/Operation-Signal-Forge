from daytona import Daytona, CreateSandboxFromSnapshotParams

def main():
    daytona = Daytona()
    
    params = CreateSandboxFromSnapshotParams(
        language='python',
        domain_allow_list='httpbin.org,example.com,api.github.com',
    )
    
    sandbox = daytona.create(params)
    print(f'✅ Sandbox ready: {sandbox.id}')
    
    print('Installing packages...')
    sandbox.process.exec('pip install httpx rich')
    
    test_code = '''
from rich import print
import httpx

print("[bold green]Signal-Forge Daytona Sandbox is live![/bold green]")

r = httpx.get('https://example.com', timeout=10)
print(f"Network test: {r.status_code}")

print("Ready for signal processing code!")
'''
    result = sandbox.process.code_run(test_code)
    print(result.result)
    
    daytona.delete(sandbox)
    print('✅ Sandbox cleaned up.')

if __name__ == '__main__':
    main()
