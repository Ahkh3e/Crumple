import os
import time
import logging
from datetime import datetime
from ..services import NetboxService
from ..models.settings import AppSettings
from ..models import db

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add file handler
if not os.path.exists('logs'):
    os.makedirs('logs')
fh = logging.FileHandler('logs/sync.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

def perform_sync(settings=None):
    """Perform a single sync operation"""
    sync_id = int(time.time() * 1000)
    logger.info(f"[Sync {sync_id}] Starting sync operation")
    
    if settings is None:
        settings = AppSettings.get_settings()
    
    try:
        if settings.netbox_url and settings.netbox_token:
            logger.info(f"[Sync {sync_id}] Using Netbox URL: {settings.netbox_url}")
            netbox = NetboxService()
            
            # Get all clusters
            start_time = time.time()
            clusters = netbox.get_clusters()
            logger.info(f"[Sync {sync_id}] Found {len(clusters)} clusters to sync")
            
            # Sync each cluster
            for cluster_data in clusters:
                cluster_id = cluster_data['id']
                logger.info(f"[Sync {sync_id}] Processing cluster {cluster_id}")
                
                try:
                    netbox.sync_cluster(cluster_id)
                except Exception as e:
                    logger.error(f"[Sync {sync_id}] Error syncing cluster {cluster_id}: {str(e)}")
                    continue
            
            # Update sync status
            elapsed = time.time() - start_time
            settings.last_sync = datetime.utcnow()
            settings.is_connected = True
            db.session.commit()
            
            logger.info(f"[Sync {sync_id}] Sync completed successfully in {elapsed:.2f}s")
            return True, None
        
        logger.error(f"[Sync {sync_id}] Netbox configuration not complete")
        return False, "Netbox configuration not complete"
        
    except Exception as e:
        logger.error(f"[Sync {sync_id}] Sync failed: {str(e)}")
        settings.is_connected = False
        db.session.commit()
        return False, str(e)

def run_sync():
    """Main sync loop"""
    logger.info("Starting sync worker")
    settings = AppSettings.get_settings()
    
    while True:
        success, error = perform_sync(settings)
        if not success:
            logger.error(f"Sync error: {error}")
            time.sleep(60)  # Wait a minute before retrying
        else:
            logger.info(f"Waiting {settings.sync_interval}s until next sync")
            time.sleep(settings.sync_interval)

if __name__ == '__main__':
    run_sync()
