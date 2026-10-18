import database.DatabaseManager;
import model.*;
import service.*;
import java.util.*;

public class Main {
    static final DatabaseManager db=new DatabaseManager();
    static final AllocationManager allocator=new AllocationManager();
    static final Scanner sc=new Scanner(System.in);

    public static void main(String[] args){
        loadSampleData();
        while(true){
            menu(); int c=readInt("Enter choice: ");
            switch(c){case 1->showData();case 2->matching();case 3->allocate();case 4->deadlines();case 5->concurrency();case 6->deadlock();case 7->recovery();case 8->AnalyticsManager.showAnalytics(db.getOrgans(),db.getAllocations(),db.getRecipients());case 9->events();case 0->{System.out.println("Program closed.");return;}default->System.out.println("Invalid choice.");}
        }
    }
    static void menu(){System.out.println("\n======================================\n ORGAN TRANSPLANT ALLOCATION SYSTEM\n======================================\n1. Show Database\n2. Find & Rank Eligible Recipients\n3. Allocate Highest-Priority Recipient\n4. Check Organ Deadlines\n5. Simulate Concurrent Claims\n6. Simulate Deadlock Detection\n7. Simulate Crash & Recovery\n8. Show Analytics\n9. Show Event Log\n0. Exit\n======================================");}
    static int readInt(String p){System.out.print(p);while(!sc.hasNextInt()){sc.next();System.out.print("Enter a number: ");}return sc.nextInt();}
    static void loadSampleData(){
        Hospital h1=new Hospital(1,"City Hospital"),h2=new Hospital(2,"Metro Hospital"),h3=new Hospital(3,"Life Care Hospital"); db.addHospital(h1);db.addHospital(h2);db.addHospital(h3);
        db.addDonor(new Donor(101,"Donor A","O+"));db.addDonor(new Donor(102,"Donor B","A+"));
        db.addOrgan(new Organ(1001,"Kidney","O+",300));db.addOrgan(new Organ(1002,"Heart","A+",300));
        db.addRecipient(new Recipient(201,"Rahul","Kidney","A+",8,30,50,h1));db.addRecipient(new Recipient(202,"Aman","Kidney","B+",9,20,100,h2));db.addRecipient(new Recipient(203,"Rohit","Kidney","AB+",7,50,30,h3));db.addRecipient(new Recipient(204,"Karan","Heart","A+",10,60,20,h1));
    }
    static void showData(){db.displayDatabase();System.out.println("\nHospitals:");db.getHospitals().forEach(System.out::println);System.out.println("\nDonors:");db.getDonors().forEach(System.out::println);System.out.println("\nRecipients:");db.getRecipients().forEach(System.out::println);}
    static ArrayList<Recipient> ranked(Organ o){ArrayList<Recipient> e=PriorityScheduler.findEligibleRecipients(o,db.getRecipients());PriorityScheduler.rankRecipients(e);return e;}
    static void matching(){Organ o=db.getOrgans().get(0);ArrayList<Recipient> e=ranked(o);System.out.println("\nOrgan: "+o.getOrganType()+" / "+o.getBloodGroup());PriorityScheduler.displayRanking(e);}
    static void allocate(){Organ o=db.getOrgans().get(0);ArrayList<Recipient> e=ranked(o);if(e.isEmpty()){System.out.println("No eligible recipient.");return;}Allocation a=allocator.allocate(o,e.get(0),e.get(0).getHospital(),db.getEvents());if(a!=null)db.addAllocation(a);}
    static void deadlines(){for(Organ o:db.getOrgans()){DeadlineScheduler.displayRemainingTime(o);DeadlineScheduler.checkDeadline(o);}}
    static void concurrency(){System.out.println("\n========== CONCURRENCY TEST ==========");Organ o=new Organ(999,"Kidney","O+",300);Recipient r1=db.getRecipients().get(0),r2=db.getRecipients().get(1);Thread t1=new Thread(()->allocator.allocate(o,r1,r1.getHospital(),db.getEvents()),"Hospital-1");Thread t2=new Thread(()->allocator.allocate(o,r2,r2.getHospital(),db.getEvents()),"Hospital-2");t1.start();t2.start();try{t1.join();t2.join();}catch(InterruptedException e){Thread.currentThread().interrupt();}System.out.println("Only one claim succeeds because allocation is synchronized on the organ.");}
    static void deadlock(){System.out.println("\n========== DEADLOCK TEST ==========");DeadlockDetector d=new DeadlockDetector();d.hospitalHoldsResource(1,101);d.hospitalHoldsResource(2,102);d.hospitalWaitsFor(1,102);d.hospitalWaitsFor(2,101);System.out.println(d.detectDeadlock()?"DEADLOCK DETECTED!":"No deadlock detected.");}
    static void recovery(){RecoveryManager.simulateCrash();RecoveryManager.recover(db.getEvents());}
    static void events(){System.out.println("\n========== EVENT LOG ==========");if(db.getEvents().isEmpty())System.out.println("No events yet.");else db.getEvents().forEach(System.out::println);}
}
