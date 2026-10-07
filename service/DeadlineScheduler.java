package service;
import model.Organ;
public class DeadlineScheduler {
    public static void checkDeadline(Organ organ){if(organ.isAllocated()||organ.isWasted())return;if(organ.isExpired()){organ.setWasted(true);System.out.println("Organ "+organ.getOrganId()+" expired -> WASTED");}}
    public static void displayRemainingTime(Organ organ){System.out.println("Organ "+organ.getOrganId()+" remaining viability: "+organ.getRemainingSeconds()+" seconds");}
}
