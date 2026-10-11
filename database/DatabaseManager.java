package database;
import model.*; import java.util.ArrayList;
public class DatabaseManager {
    private final ArrayList<Hospital> hospitals=new ArrayList<>(); private final ArrayList<Donor> donors=new ArrayList<>(); private final ArrayList<Recipient> recipients=new ArrayList<>(); private final ArrayList<Organ> organs=new ArrayList<>(); private final ArrayList<Allocation> allocations=new ArrayList<>(); private final ArrayList<AllocationEvent> events=new ArrayList<>();
    public void addHospital(Hospital x){hospitals.add(x);} public void addDonor(Donor x){donors.add(x);} public void addRecipient(Recipient x){recipients.add(x);} public void addOrgan(Organ x){organs.add(x);} public void addAllocation(Allocation x){allocations.add(x);}
    public ArrayList<Hospital> getHospitals(){return hospitals;} public ArrayList<Donor> getDonors(){return donors;} public ArrayList<Recipient> getRecipients(){return recipients;} public ArrayList<Organ> getOrgans(){return organs;} public ArrayList<Allocation> getAllocations(){return allocations;} public ArrayList<AllocationEvent> getEvents(){return events;}
    public void displayDatabase(){System.out.println("\nDB COUNTS -> Hospitals: "+hospitals.size()+", Donors: "+donors.size()+", Recipients: "+recipients.size()+", Organs: "+organs.size()+", Allocations: "+allocations.size()+", Events: "+events.size());}
}
