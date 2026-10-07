package model;
import java.time.LocalDateTime;
public class Allocation {
    private final int allocationId,organId,recipientId,hospitalId; private final LocalDateTime allocationTime; private final String status,reason;
    public Allocation(int allocationId,int organId,int recipientId,int hospitalId,String status,String reason){this.allocationId=allocationId;this.organId=organId;this.recipientId=recipientId;this.hospitalId=hospitalId;this.status=status;this.reason=reason;this.allocationTime=LocalDateTime.now();}
    public int getAllocationId(){return allocationId;} public int getOrganId(){return organId;} public int getRecipientId(){return recipientId;} public int getHospitalId(){return hospitalId;} public LocalDateTime getAllocationTime(){return allocationTime;} public String getStatus(){return status;} public String getReason(){return reason;}
    public String toString(){return "Allocation ID: "+allocationId+", Organ: "+organId+", Recipient: "+recipientId+", Hospital: "+hospitalId+", Status: "+status+", Reason: "+reason+", Time: "+allocationTime;}
}
