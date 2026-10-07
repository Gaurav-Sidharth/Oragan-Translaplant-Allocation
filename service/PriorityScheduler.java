package service;
import model.Organ; import model.Recipient; import java.util.ArrayList;
public class PriorityScheduler {
    public static ArrayList<Recipient> findEligibleRecipients(Organ organ,ArrayList<Recipient> recipients){ArrayList<Recipient> out=new ArrayList<>();for(Recipient r:recipients){if(r.getOrganType().equalsIgnoreCase(organ.getOrganType())&&CompatibilityChecker.isCompatible(organ.getBloodGroup(),r.getBloodGroup()))out.add(r);}return out;}
    public static void rankRecipients(ArrayList<Recipient> list){list.sort((a,b)->Double.compare(b.calculatePriority(),a.calculatePriority()));}
    public static void displayRanking(ArrayList<Recipient> list){System.out.println("\n========== PRIORITY QUEUE ==========");int rank=1;for(Recipient r:list)System.out.printf("Rank %d -> %s | Hospital: %s | Priority: %.2f%n",rank++,r.getName(),r.getHospital().getName(),r.calculatePriority());System.out.println("====================================");}
}
