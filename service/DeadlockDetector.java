package service;
import java.util.*;
public class DeadlockDetector {
    private final Map<Integer,Integer> waitingFor=new HashMap<>(); private final Map<Integer,Integer> holding=new HashMap<>();
    public void hospitalHoldsResource(int hospital,int resource){holding.put(hospital,resource);}
    public void hospitalWaitsFor(int hospital,int resource){waitingFor.put(hospital,resource);}
    public boolean detectDeadlock(){for(Integer h:waitingFor.keySet())if(hasCycle(h,new HashSet<>()))return true;return false;}
    private boolean hasCycle(int h,Set<Integer> visited){if(visited.contains(h))return true;visited.add(h);Integer resource=waitingFor.get(h);if(resource==null){visited.remove(h);return false;}for(Map.Entry<Integer,Integer> e:holding.entrySet())if(e.getValue().equals(resource)&&hasCycle(e.getKey(),visited))return true;visited.remove(h);return false;}
    public void clear(){waitingFor.clear();holding.clear();}
}
