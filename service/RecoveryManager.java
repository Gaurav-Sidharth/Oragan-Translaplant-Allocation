package service;
import model.AllocationEvent; import java.util.ArrayList;
public class RecoveryManager {
    public static void simulateCrash(){System.out.println("\n*** CRASH SIMULATION ***");System.out.println("Application stopped unexpectedly. Persistent event log is retained.");}
    public static void recover(ArrayList<AllocationEvent> events){System.out.println("\n*** RECOVERY ***");System.out.println("Replaying allocation events:");for(AllocationEvent e:events)System.out.println(e);System.out.println("Recovery replay completed.");}
}
