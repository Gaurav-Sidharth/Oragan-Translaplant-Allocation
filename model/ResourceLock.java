package model;
public class ResourceLock {
    private final int resourceId; private final String resourceName; private int lockedByHospital=-1; private boolean locked;
    public ResourceLock(int resourceId,String resourceName){this.resourceId=resourceId;this.resourceName=resourceName;}
    public synchronized boolean acquire(int hospitalId){if(!locked){locked=true;lockedByHospital=hospitalId;return true;}return false;}
    public synchronized void release(int hospitalId){if(lockedByHospital==hospitalId){locked=false;lockedByHospital=-1;}}
    public int getResourceId(){return resourceId;} public String getResourceName(){return resourceName;} public boolean isLocked(){return locked;} public int getLockedByHospital(){return lockedByHospital;}
}
