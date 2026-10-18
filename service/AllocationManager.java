package service;
import model.*; import java.util.ArrayList; import java.util.concurrent.atomic.AtomicInteger;
public class AllocationManager {
    private final AtomicInteger counter=new AtomicInteger(1);
    public Allocation allocate(Organ organ,Recipient recipient,Hospital hospital,ArrayList<AllocationEvent> events){
        synchronized(organ){
            System.out.println(hospital.getName()+" attempting claim for organ "+organ.getOrganId());
            if(organ.isAllocated()){add(events,"CLAIM_FAILED","Organ already allocated");return null;}
            if(organ.isExpired()){organ.setWasted(true);add(events,"ORGAN_EXPIRED","Organ expired before allocation");return null;}
            organ.setAllocated(true); Allocation a=new Allocation(counter.getAndIncrement(),organ.getOrganId(),recipient.getRecipientId(),hospital.getHospitalId(),"ALLOCATED","Compatible recipient with highest priority");add(events,"ALLOCATED","Organ "+organ.getOrganId()+" allocated to "+recipient.getName());System.out.println("SUCCESS -> "+recipient.getName());return a;
        }
    }
    private void add(ArrayList<AllocationEvent> e,String type,String desc){synchronized(e){e.add(new AllocationEvent(e.size()+1,type,desc));}}
}
