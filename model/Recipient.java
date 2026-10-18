package model;
public class Recipient {
    private final int recipientId; private final String name,organType,bloodGroup; private final int urgencyScore,waitingDays; private final double distance; private final Hospital hospital;
    public Recipient(int recipientId,String name,String organType,String bloodGroup,int urgencyScore,int waitingDays,double distance,Hospital hospital){this.recipientId=recipientId;this.name=name;this.organType=organType;this.bloodGroup=bloodGroup;this.urgencyScore=urgencyScore;this.waitingDays=waitingDays;this.distance=distance;this.hospital=hospital;}
    public int getRecipientId(){return recipientId;} public String getName(){return name;} public String getOrganType(){return organType;} public String getBloodGroup(){return bloodGroup;} public int getUrgencyScore(){return urgencyScore;} public int getWaitingDays(){return waitingDays;} public double getDistance(){return distance;} public Hospital getHospital(){return hospital;}
    public double calculatePriority(){return urgencyScore*10.0+waitingDays*2.0-distance;}
    public String toString(){return "ID: "+recipientId+", Name: "+name+", Organ: "+organType+", Blood: "+bloodGroup+", Urgency: "+urgencyScore+", Waiting: "+waitingDays+", Distance: "+distance+", Priority: "+calculatePriority();}
}
