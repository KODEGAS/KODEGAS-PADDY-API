# Production Deployment Guide: FastAPI on Azure VM with Nginx

This guide will walk you through deploying your Paddy Disease API application on an Azure Virtual Machine (VM) using Docker and Nginx as a reverse proxy.

### Prerequisites

- **GitHub Student Developer Pack**: Ensure you have activated it.
- **Azure for Students**: You will use this to create your resources. If you haven't activated it, sign up here: [https://azure.microsoft.com/en-us/free/students/](https://azure.microsoft.com/en-us/free/students/)

---

### Step 1: Create an Azure Virtual Machine

1.  **Sign in to the Azure Portal**: [https://portal.azure.com/](https://portal.azure.com/)
2.  **Create a Virtual Machine**:
    *   Click on **"Create a resource"** and search for **"Virtual machine"**.
    *   **Subscription**: Choose your "Azure for Students" subscription.
    *   **Resource group**: Create a new one (e.g., `paddy-api-rg`).
    *   **Virtual machine name**: Give it a name (e.g., `paddy-api-vm`).
    *   **Region**: Choose a region close to you.
    *   **Image**: Select **Ubuntu Server 22.04 LTS**.
    *   **Size**: Select the **Standard_B1s** size. This is a burstable VM that is typically included in the Azure free tier and covered by your "Azure for Students" credits. It provides 1 vCPU and 1 GiB of memory, which is sufficient for this application. Avoid larger sizes like `D2s_v3` to stay within your free credits.
    *   **Authentication type**: Select **"SSH public key"**.
    *   **SSH public key**: Provide your public SSH key. If you don't have one, you can generate it on your local machine using `ssh-keygen -t rsa -b 2048`.
3.  **Configure Networking**:
    *   Go to the **"Networking"** tab.
    *   Under **"NIC network security group"**, click **"Advanced"**.
    *   Click **"Create new"** to configure the inbound rules.
    *   Add inbound rules to allow traffic on these ports:
        *   **Port 22 (SSH)**: To connect to your VM.
        *   **Port 80 (HTTP)**: For web traffic.
        *   **Port 443 (HTTPS)**: For secure web traffic (optional, for later).
4.  **Review and Create**: Click **"Review + create"** and then **"Create"**. Azure will deploy your VM.

---

### Step 2: Connect to Your VM and Install Dependencies

1.  **Find your VM's IP Address**: In the Azure portal, go to your VM's overview page and copy the "Public IP address".
2.  **Connect via SSH**: Open a terminal on your local machine and connect using:
    ```bash
    ssh <your-username>@<your-vm-ip-address>
    ```
3.  **Install Docker**: Run the following commands to install Docker, which will be used to run your application container.
    ```bash
    sudo apt-get update
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER 
    # You may need to log out and log back in for the group change to take effect.
    ```
4.  **Install Nginx**: This will act as our reverse proxy.
    ```bash
    sudo apt-get install -y nginx
    sudo systemctl start nginx
    ```

---

### Step 3: Deploy Your Application

1.  **Clone Your Repository**: Clone your application code from GitHub onto the VM.
    ```bash
    git clone https://github.com/kavindus0/paddy_disease_api.git
    cd paddy_disease_api
    ```
2.  **Build the Docker Image**: Your repository already contains a `Dockerfile`. Build the image from it. You'll need to use `sudo` to grant Docker the necessary permissions.
    ```bash
    sudo docker build -t paddy-api-image .
    ```
3.  **Run the Docker Container**: Run your application inside a Docker container. This command starts the container in detached mode and maps port 8000 inside the container to port 8000 on the VM.
    ```bash
    sudo docker run -d --name paddy-api-container -p 127.0.0.1:8000:8000 paddy-api-image
    ```
    *Note: We bind to `127.0.0.1` (localhost) on the VM because we only want Nginx to be able to access it directly. The outside world will go through Nginx.*

---

### Step 4: Configure Nginx as a Reverse Proxy

Nginx will listen for public traffic on port 80 and forward it to your application running on port 8000.

1.  **Create an Nginx Configuration File**:
    ```bash
    sudo nano /etc/nginx/sites-available/paddy_disease_api
    ```
2.  **Add the following configuration**: This tells Nginx to pass requests to your Gunicorn server.
    ```nginx
    server {
        listen 80;
        server_name <your-vm-ip-address>; # Or your domain name if you have one

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```
3.  **Enable the Configuration**:
    *   Disable the default Nginx configuration:
        ```bash
        sudo rm /etc/nginx/sites-enabled/default
        ```
    *   Create a symbolic link to enable your new configuration:
        ```bash
        sudo ln -s /etc/nginx/sites-available/paddy_disease_api /etc/nginx/sites-enabled/
        ```
4.  **Test and Restart Nginx**:
    *   Check for syntax errors in your Nginx configuration:
        ```bash
        sudo nginx -t
        ```
    *   If the test is successful, restart Nginx to apply the changes:
        ```bash
        sudo systemctl restart nginx
        ```

---

### Step 5: Access Your Application

You should now be able to access your application by navigating to your VM's public IP address in a web browser.

`http://<your-vm-ip-address>`

Congratulations, your application is now deployed and ready for production!

---

### Step 6: Updating Your Application

When you want to update an HTML file or any other part of your application, follow these steps:

1.  **Make Changes Locally**: Edit the files on your local machine as you normally would.
2.  **Commit and Push to GitHub**:
    ```bash
    git add .
    git commit -m "Your update message"
    git push origin main
    ```
3.  **Update on the VM**:
    *   Connect to your Azure VM via SSH.
    *   Navigate to your project directory: `cd paddy_disease_api`
    *   Pull the latest changes from your repository:
        ```bash
        git pull origin main
        ```
4.  **Rebuild and Restart the Docker Container**:
    *   Stop and remove the old container:
        ```bash
        sudo docker stop paddy-api-container
        sudo docker rm paddy-api-container
        ```
    *   Rebuild the image with your changes:
        ```bash
        sudo docker build -t paddy-api-image .
        ```
    *   Run the new container:
        ```bash
        sudo docker run -d --name paddy-api-container -p 127.0.0.1:8000:8000 paddy-api-image
        ```

Your updated application will now be live.

---

### Step 7: Automating Deployments with GitHub Actions

You can automate the update process using GitHub Actions. This will automatically deploy your changes every time you push to your `main` branch.

1.  **Add Secrets to Your GitHub Repository**:
    *   Go to your repository on GitHub and click on **"Settings"** > **"Secrets and variables"** > **"Actions"**.
    *   Click **"New repository secret"** to add the following secrets:
        *   `AZURE_VM_HOST`: The public IP address of your Azure VM.
        *   `AZURE_VM_USERNAME`: The username you use to SSH into your VM.
        *   `AZURE_VM_SSH_KEY`: Your private SSH key that corresponds to the public key you added to the VM.

2.  **Commit the Workflow File**: The `.github/workflows/deploy.yml` file has already been created for you. Commit and push it to your repository.

Now, every time you push a change to your `main` branch, the GitHub Actions workflow will automatically connect to your VM, pull the latest code, and redeploy your application.

---

### Step 8: Setting Up SSL with Certbot (Free HTTPS)

Securing your application with HTTPS is crucial for production. We'll use Certbot with Let's Encrypt to get a free SSL certificate.

1.  **Install Certbot**: Connect to your VM via SSH and run the following commands to install Certbot and its Nginx plugin.
    ```bash
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
    ```

2.  **Verify Firewall Rules**: The error you encountered indicates a firewall issue. Let's ensure your Azure firewall allows HTTP and HTTPS traffic.
    *   Go to the **Azure Portal** and navigate to your virtual machine.
    *   In the left menu, click on **"Networking"**.
    *   Look at the **"Inbound port rules"**. You must have rules that allow traffic for both **HTTP (port 80)** and **HTTPS (port 443)**.
    *   If they are missing, click **"Add inbound port rule"** and create them:
        *   **Source**: `Any`
        *   **Source port ranges**: `*`
        *   **Destination**: `Any`
        *   **Service**: `HTTP` (or select `TCP` and port `80`)
        *   **Action**: `Allow`
        *   **Priority**: A number like `300`
        *   **Name**: `Allow-HTTP`
    *   Repeat the process for **HTTPS (port 443)**.

3.  **Run Certbot**: Once you've confirmed the firewall rules are in place, run Certbot. It will automatically detect your domain from your Nginx configuration, obtain a certificate, and configure Nginx for you.
    ```bash
    sudo certbot --nginx -d kodegas-paddy-api.centralindia.cloudapp.azure.com
    ```
    *   Certbot will ask for your email address and for you to agree to the terms of service.
    *   When prompted, choose to **redirect HTTP traffic to HTTPS**. This is the recommended option for security.

4.  **Verify Automatic Renewal**: Certbot automatically sets up a scheduled task to renew your certificate before it expires. You can test the renewal process with this command:
    ```bash
    sudo certbot renew --dry-run
    ```

Your application should now be accessible via `https://kodegas-paddy-api.centralindia.cloudapp.azure.com`, and all traffic will be securely encrypted.
