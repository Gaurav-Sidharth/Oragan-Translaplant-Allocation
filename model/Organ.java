package model;
public class Organ {
    private final int organId; private final String organType,bloodGroup; private final long expiryTime; private boolean allocated,wasted;
    public Organ(int organId,String organType,String bloodGroup,long viabilitySeconds){this.organId=organId;this.organType=organType;this.bloodGroup=bloodGroup;this.expiryTime=System.currentTimeMillis()+viabilitySeconds*1000L;}
    public int getOrganId(){return organId;} public String getOrganType(){return organType;} public String getBloodGroup(){return bloodGroup;} public long getExpiryTime(){return expiryTime;} public boolean isAllocated(){return allocated;} public boolean isWasted(){return wasted;}
    public void setAllocated(boolean v){allocated=v;} public void setWasted(boolean v){wasted=v;} public boolean isExpired(){return System.currentTimeMillis()>=expiryTime;} public long getRemainingSeconds(){return Math.max(0,(expiryTime-System.currentTimeMillis())/1000);}
}
